from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView

from .models import Item, OrderItem, Order


class HomeView(ListView):
    template_name = "home.html"
    paginate_by = 8
    model = Item


class OrderDetailView(LoginRequiredMixin, TemplateView):
    template_name = "checkout-page.html"

    def get(self, request, *args, **kwargs):
        try:
            self.order = self.request.user.orders.get(is_ordered=False)
        except:
            return redirect('core:home')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['items'] = self.order.order_items.all().prefetch_related('item')
        data['order'] = self.order
        return data


class ItemDetailView(DetailView):
    template_name = "product-page.html"
    model = Item


@login_required
def add_to_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
    else:
        order = Order.objects.create(user=request.user)
    order.add_item(item_id)

    return redirect("core:product", slug=item.slug)


@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    order_qs = Order.objects.filter(user=request.user, is_ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        order.remove_item(item.id)

    return redirect("core:checkout")
