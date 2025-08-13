from django.contrib import admin
from .models import Product, Customer, Purchase, PurchaseItem, Denomination, BalanceDenomination

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'name', 'available_stocks', 'price_per_unit', 'tax_percentage']
    list_filter = ['tax_percentage', 'created_at']
    search_fields = ['product_id', 'name']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['email', 'created_at']
    search_fields = ['email']

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0
    readonly_fields = ['tax_amount', 'total_price']

class BalanceDenominationInline(admin.TabularInline):
    model = BalanceDenomination
    extra = 0

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['purchase_id', 'customer', 'net_amount', 'created_at']
    list_filter = ['created_at']
    search_fields = ['purchase_id', 'customer__email']
    readonly_fields = ['purchase_id', 'created_at']
    inlines = [PurchaseItemInline, BalanceDenominationInline]

@admin.register(Denomination)
class DenominationAdmin(admin.ModelAdmin):
    list_display = ['value', 'count']
    ordering = ['-value']