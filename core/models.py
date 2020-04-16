from django.conf import settings
from django.db import models, transaction
from django.db.models import Sum
from django.template.defaultfilters import slugify
from django.urls import reverse
from django_countries.fields import CountryField

CATEGORY_CHOICES = (
    ('S', 'Sexy'),
    ('SW', 'Fine'),
    ('OW', 'Magical')
)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2, default='S')
    label = models.CharField(choices=LABEL_CHOICES, max_length=1, default='P')
    slug = models.SlugField(unique=True, null=False)
    description = models.TextField(default='Very durable and hot product')
    stock = models.IntegerField(default=1)
    image = models.ImageField(null=True, blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('core:product', kwargs={
            'slug': self.slug
        })

    def get_add_single_to_cart_url(self):
        return reverse('core:add-single-to-cart', kwargs={
            'item_id': self.id
        })

    def get_remove_single_from_cart_url(self):
        return reverse('core:remove-single-from-cart', kwargs={
            'item_id': self.id
        })

    def get_remove_from_cart_url(self):
        return reverse('core:remove-from-cart', kwargs={
            'item_id': self.id
        })

    def save(self, *args, **kwargs): # new
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('S', 'Stripe'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_ordered = models.DateTimeField(null=True)
    is_ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, null=True)
    payment_option = models.CharField(choices=PAYMENT_CHOICES, max_length=2, null=True)

    def __str__(self):
        return f'{self.id}-{self.is_ordered}'

    @property
    def total_price(self):
        price = 0
        for order_item in self.order_items.all():
            price += order_item.total_item_price
        return price

    @property
    def total_count(self):
        count = 0
        for order_item in self.order_items.all():
            count += 1 * order_item.quantity
        return count

    @transaction.atomic
    def add_single_item(self, item_id):
        try:
            item = Item.objects.get(id=item_id, stock__gt=0)
        except Item.DoesNotExist:
            return None

        item.stock -= 1
        item.save()
        if self.order_items.filter(item__id=item_id).exists():
            order_item = self.order_items.get(item__id=item_id)
            order_item.quantity += 1
            order_item.save()
        else:
            OrderItem.objects.create(item=item, order=self)

    @transaction.atomic
    def remove_single_item(self, item_id):
        try:
            order_item = self.order_items.get(item__id=item_id)
        except Item.DoesNotExist:
            return None

        if order_item.quantity > 1:
            order_item.quantity -= 1
            order_item.save()
        else:
            order_item.delete()

        order_item.item.stock += 1
        order_item.item.save()

    @transaction.atomic
    def remove_item(self, item_id):
        try:
            order_item = self.order_items.get(item__id=item_id)
        except Item.DoesNotExist:
            return None

        order_item.delete()
        order_item.item.stock += order_item.quantity
        order_item.item.save()


class OrderItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return self.title

    @property
    def total_item_price(self):
        return self.quantity * self.item.price


class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
