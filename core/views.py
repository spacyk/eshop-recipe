import stripe
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView, View

from .forms import CheckoutForm
from .models import Item, OrderItem, Order, BillingAddress


class HomeView(ListView):
    template_name = "home.html"
    paginate_by = 8
    model = Item


class PaymentView(AccessMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            self.order = Order.objects.get(user=self.request.user, is_ordered=False)
        except Order.DoesNotExist:
            return HttpResponseRedirect(reverse('core:home'))
        else:
            if self.order.total_count == 0:
                return HttpResponseRedirect(reverse('core:home'))

        self.intent = self.request.session.get('intent')
        if not self.intent:
            return HttpResponseRedirect(reverse('core:home'))

        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        context = {
            'order': self.order,
            'intent': self.intent
        }
        return render(self.request, "payment.html", context)

    def post(self, *args, payment_option=None, **kwargs):
        return redirect(reverse('core:payment', kwargs={'payment_option': payment_option}))


class CheckoutView(AccessMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            self.order = Order.objects.get(user=self.request.user, is_ordered=False)
        except Order.DoesNotExist:
            return HttpResponseRedirect(reverse('core:home'))
        else:
            if self.order.total_count == 0:
                return HttpResponseRedirect(reverse('core:home'))

        return super().dispatch(request, *args, **kwargs)

    def get(self, *args, **kwargs):
        address = self.order.billing_address
        form_data = {}
        if address:
            form_data.update(
                street_address=address.street_address,
                country=address.country,
                zip=address.zip
            )
        if self.order.payment_option:
            form_data.update(payment_option=self.order.payment_option)
        form = CheckoutForm(data=form_data)
        context = {
            'form': form,
            'items': self.order.order_items.all().prefetch_related('item'),
            'order': self.order
        }
        return render(self.request, "checkout-page.html", context)

    @transaction.atomic
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        if form.is_valid():
            street_address = form.cleaned_data.get('street_address')
            country = form.cleaned_data.get('country')
            zip = form.cleaned_data.get('zip')
            payment_option = form.cleaned_data.get('payment_option')
            try:
                billing_address = BillingAddress.objects.get(user=self.request.user, street_address=street_address, country=country, zip=zip)
            except BillingAddress.DoesNotExist:
                billing_address = BillingAddress.objects.create(user=self.request.user, street_address=street_address, country=country, zip=zip)

            self.order.billing_address = billing_address
            self.order.payment_option = payment_option
            self.order.save(update_fields=['billing_address', 'payment_option'])

            self.create_stripe_intent()
            # Think of this as, instruction guy performs actual payment on banckend
            # Confirm payment could be handled by backend... maybe better way
            return redirect(reverse('core:payment', kwargs={'payment_option': payment_option}))

        return render(self.request, "checkout-page.html")

    def create_stripe_intent(self):
        intent = self.request.session.get('intent')
        actual_price = int(self.order.total_price * 100)
        if intent:
            stripe.PaymentIntent.modify(
                intent.get('id'),
                amount=actual_price,
            )
        else:
            intent = stripe.PaymentIntent.create(
                amount=actual_price,
                currency='czk',
                # Verify your integration in this guide by including this parameter
                metadata={'integration_check': 'accept_a_payment'},
            )
            self.request.session['intent'] = {'client_secret': intent.client_secret, 'id': intent.id}


class ItemDetailView(DetailView):
    template_name = "product-page.html"
    model = Item


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, is_ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order-summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You don't have an active order")
            return HttpResponseRedirect(reverse('core:home'))


def _remove_single(request, item):
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order.remove_single_item(item.id)


def _add_single(request, item):
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
    else:
        order = Order.objects.create(user=request.user)
    order.add_single_item(item.id)


@login_required
def add_single_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    _add_single(request, item)

    return HttpResponseRedirect(reverse('core:product', kwargs={'slug': item.slug}))


@login_required
def remove_single_from_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    _remove_single(request, item)

    return HttpResponseRedirect(reverse('core:product', kwargs={'slug': item.slug}))


@login_required
def summary_add_single_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    _add_single(request, item)

    return HttpResponseRedirect(reverse('core:order-summary'))


@login_required
def summary_remove_single_from_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    _remove_single(request, item)

    return HttpResponseRedirect(reverse('core:order-summary'))


@login_required
def summary_remove_from_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order.remove_item(item.id)

    return HttpResponseRedirect(reverse('core:order-summary'))
