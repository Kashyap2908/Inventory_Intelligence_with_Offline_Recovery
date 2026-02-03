from django.contrib import admin
from .models import Product, ExpiryStock, OrderQueue, SalesBill, SalesBillItem, UserProfile, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'cost_price', 'selling_price', 'new_price', 'abc_classification', 'trend_score']
    list_filter = ['abc_classification', 'category']
    search_fields = ['name', 'category']

@admin.register(ExpiryStock)
class ExpiryStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'expiry_date', 'created_at']
    list_filter = ['expiry_date', 'created_at']

@admin.register(OrderQueue)
class OrderQueueAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'created_at']

@admin.register(SalesBill)
class SalesBillAdmin(admin.ModelAdmin):
    list_display = ['bill_number', 'total_amount', 'created_at']
    readonly_fields = ['bill_number']

@admin.register(SalesBillItem)
class SalesBillItemAdmin(admin.ModelAdmin):
    list_display = ['bill', 'product', 'quantity', 'price', 'total']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'notification_type', 'priority', 'target_user_role', 'product', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'target_user_role', 'is_read', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')