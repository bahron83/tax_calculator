from django.contrib import admin
from tax_calculator.models import TaxRate, ProductCategory, Product, Cart, CartItem


class TaxRateAdmin(admin.ModelAdmin):
    model = TaxRate
    list_display_links = ('id',)
    list_display = ('id', 'code', 'name', 'amount', 'mode')

class ProductCategoryAdmin(admin.ModelAdmin):
    model = ProductCategory
    list_display_links = ('id',)
    list_display = ('id', 'name',)

class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display_links = ('id',)
    list_display = ('id', 'code', 'name', 'base_price')

class CartItemInline(admin.StackedInline):
    model = CartItem
    extra = 1

class CartAdmin(admin.ModelAdmin):
    model = Cart
    list_display_links = ('id',)
    list_display = ('id', 'customer', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at',)
    inlines = [CartItemInline]

admin.site.register(TaxRate, TaxRateAdmin)
admin.site.register(ProductCategory, ProductCategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart, CartAdmin)
