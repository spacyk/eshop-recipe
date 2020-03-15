from django.contrib import admin
from .models import Item, OrderItem, Order


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}


admin.site.register(OrderItem)
admin.site.register(Order)
