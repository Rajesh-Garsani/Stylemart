from django.contrib import admin
from .models import Category, Product, UserProfile, Cart, Order, OrderItem


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("name", "category__name")
    list_editable = ("price", "stock")
    readonly_fields = ("created_at",)



class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1



class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__username", "phone")
    inlines = [OrderItemInline]



admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(UserProfile)
admin.site.register(Cart)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
