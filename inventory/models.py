from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('inventory', 'Inventory Manager'),
        ('marketing', 'Marketing Manager'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Product(models.Model):
    ABC_CHOICES = [
        ('A', 'A - High Value'),
        ('B', 'B - Medium Value'),
        ('C', 'C - Low Value'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    abc_classification = models.CharField(max_length=1, choices=ABC_CHOICES, default='C')
    trend_score = models.FloatField(default=0.0)
    discount_percentage = models.FloatField(default=0.0)
    last_trend_update = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    @property
    def total_stock(self):
        from datetime import date
        # Only count non-expired stock
        return sum(
            stock.quantity for stock in self.expirystock_set.filter(
                quantity__gt=0,
                expiry_date__gte=date.today()  # Only include non-expired stock
            )
        )
    
    @property
    def expired_stock(self):
        from datetime import date
        # Count expired stock
        return sum(
            stock.quantity for stock in self.expirystock_set.filter(
                quantity__gt=0,
                expiry_date__lt=date.today()  # Only expired stock
            )
        )
    
    @property
    def days_to_nearest_expiry(self):
        from datetime import date
        # Only consider non-expired stock with quantity > 0
        nearest = self.expirystock_set.filter(
            quantity__gt=0,
            expiry_date__gte=date.today()  # Only non-expired stock
        ).order_by('expiry_date').first()
        
        if nearest:
            return (nearest.expiry_date - date.today()).days
        return None

class ExpiryStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['expiry_date']

class OrderQueue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SalesBill(models.Model):
    bill_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class SalesBillItem(models.Model):
    bill = models.ForeignKey(SalesBill, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('expiry_warning', 'Expiry Warning'),
        ('low_stock', 'Low Stock'),
        ('overstock', 'Overstock Alert'),
        ('reorder_needed', 'Reorder Needed'),
        ('admin_message', 'Admin Message'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    target_user_role = models.CharField(max_length=20, default='inventory')  # inventory, marketing, admin, all
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Track when notification was last updated (marked as read)
    expires_at = models.DateTimeField(null=True, blank=True)  # Auto-delete after this time
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.priority}"
    
    @property
    def safe_updated_at(self):
        """Safely get updated_at field, fallback to created_at if not available"""
        # Use updated_at if available, otherwise fallback to created_at
        if hasattr(self, 'updated_at') and self.updated_at:
            return self.updated_at
        return self.created_at


class AIRecommendation(models.Model):
    """Track AI recommendations and their status"""
    RECOMMENDATION_TYPES = [
        ('increase_stock', 'Increase Stock'),
        ('raise_price', 'Raise Price'),
        ('apply_discount', 'Apply Discount'),
        ('reduce_orders', 'Reduce Orders'),
        ('reorder_soon', 'Reorder Soon'),
        ('monitor', 'Monitor'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('applied', 'Applied'),
        ('dismissed', 'Dismissed'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    recommendation_text = models.TextField()
    trend_score = models.FloatField()
    stock_level = models.IntegerField()
    suggested_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # For price/discount %
    suggested_quantity = models.IntegerField(null=True, blank=True)  # For stock quantity
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_by = models.CharField(max_length=100, null=True, blank=True)  # Username who applied/dismissed
    applied_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'recommendation_type', 'status']  # Prevent duplicate pending recommendations
    
    def __str__(self):
        return f"{self.product.name} - {self.get_recommendation_type_display()} ({self.status})"