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
    store_name = models.CharField(max_length=100, blank=True, null=True)  # Store/Location name
    store_location = models.CharField(max_length=200, blank=True, null=True)  # Full address
    phone_number = models.CharField(max_length=15, blank=True, null=True)  # Contact number
    
    def __str__(self):
        store_info = f" - {self.store_name}" if self.store_name else ""
        return f"{self.user.username} ({self.role}){store_info}"
    
    @property
    def display_name(self):
        """Get user's display name"""
        if self.user.first_name:
            return f"{self.user.first_name} {self.user.last_name}".strip()
        return self.user.username
    
    @property
    def full_identity(self):
        """Get complete identity with store"""
        name = self.display_name
        if self.store_name:
            return f"{name} ({self.store_name})"
        return name

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
        # Only count non-expired stock (all users combined)
        return sum(
            stock.quantity for stock in self.expirystock_set.filter(
                quantity__gt=0,
                expiry_date__gte=date.today()  # Only include non-expired stock
            )
        )
    
    def get_user_stock(self, user):
        """Get stock for a specific user"""
        from datetime import date
        return sum(
            stock.quantity for stock in self.expirystock_set.filter(
                user=user,
                quantity__gt=0,
                expiry_date__gte=date.today()
            )
        )
    
    def get_all_users_stock(self):
        """Get stock breakdown by user"""
        from datetime import date
        from django.db.models import Sum
        
        stock_by_user = self.expirystock_set.filter(
            user__isnull=False,  # Exclude stock without user assignment
            quantity__gt=0,
            expiry_date__gte=date.today()
        ).values('user__username', 'user__first_name', 'user__last_name').annotate(
            total=Sum('quantity')
        ).order_by('-total')
        
        return stock_by_user
    
    def get_company_stock(self):
        """Get company warehouse stock (admin's stock)"""
        from datetime import date
        from django.contrib.auth.models import User
        try:
            company_user = User.objects.get(username='company_stock')
            return self.get_user_stock(company_user)
        except User.DoesNotExist:
            return 0
    
    def get_inventory_users_stock(self):
        """Get total stock across all inventory users (excluding company)"""
        from datetime import date
        return sum(
            stock.quantity for stock in self.expirystock_set.filter(
                user__isnull=False,
                user__userprofile__role='inventory',
                quantity__gt=0,
                expiry_date__gte=date.today()
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
    
    @property
    def calculated_abc_classification(self):
        """Calculate ABC classification based on trend score"""
        if self.trend_score >= 7.0:
            return 'A'
        elif self.trend_score >= 4.0:
            return 'B'
        else:
            return 'C'

class ExpiryStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Track which inventory user owns this stock
    
    class Meta:
        ordering = ['expiry_date']
    
    def __str__(self):
        user_name = self.user.username if self.user else "Unassigned"
        return f"{self.product.name} - {self.quantity} units (Expires: {self.expiry_date}) - Owner: {user_name}"

class OrderQueue(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved by Admin'),
        ('partially_fulfilled', 'Partially Fulfilled'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    INVENTORY_ACTION_CHOICES = [
        ('none', 'No Action'),
        ('acknowledged', 'Acknowledged'),
        ('ordered', 'Ordered with Supplier'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()  # Requested quantity by inventory
    approved_quantity = models.IntegerField(null=True, blank=True)  # Quantity approved by admin
    fulfilled_quantity = models.IntegerField(default=0)  # Quantity actually sent/fulfilled
    pending_quantity = models.IntegerField(default=0)  # Remaining quantity to be sent
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    expected_delivery_date = models.DateField(null=True, blank=True)  # When user can expect delivery
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # New fields for enhanced workflow
    ordered_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)  # Admin who created order OR Inventory who requested
    requested_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True, related_name='inventory_requests')  # Inventory user who requested
    message_sent = models.BooleanField(default=False)  # Whether notification was sent to inventory
    message_received = models.BooleanField(default=False)  # Whether inventory acknowledged the message
    message_received_at = models.DateTimeField(null=True, blank=True)  # When inventory acknowledged
    order_notes = models.TextField(blank=True, null=True)  # Additional notes from admin
    
    # New fields for inventory action tracking
    inventory_action = models.CharField(max_length=20, choices=INVENTORY_ACTION_CHOICES, default='none')  # What inventory did
    inventory_action_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_actions')  # Who from inventory took action
    inventory_action_at = models.DateTimeField(null=True, blank=True)  # When inventory took action
    admin_marked_received = models.BooleanField(default=False)  # Whether admin marked as received (final step)
    admin_marked_received_at = models.DateTimeField(null=True, blank=True)  # When admin marked as received
    
    # Bill tracking
    bill_generated = models.BooleanField(default=False)  # Whether bill was auto-generated
    bill = models.ForeignKey('SalesBill', on_delete=models.SET_NULL, null=True, blank=True, related_name='order_requests')  # Link to generated bill
    
    def __str__(self):
        return f"Order: {self.product.name} - {self.quantity} units ({self.status})"

class SalesBill(models.Model):
    bill_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)  # Track who created the bill

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


class LowStockThreshold(models.Model):
    """User-specific low stock thresholds for products"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    threshold = models.IntegerField(default=10)  # Alert when stock goes below this
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} (Threshold: {self.threshold})"

class StockMovement(models.Model):
    """Complete audit trail of all stock movements"""
    MOVEMENT_TYPES = [
        ('add', 'Stock Added'),
        ('deduct', 'Stock Deducted'),
        ('transfer_out', 'Transferred Out'),
        ('transfer_in', 'Transferred In'),
        ('damage', 'Damaged/Lost'),
        ('return', 'Returned'),
        ('adjustment', 'Manual Adjustment'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Who performed the action
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField()
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transfers_out')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_transfers_in')
    reason = models.TextField(blank=True, null=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)  # Bill number, order ID, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.movement_type} - {self.product.name} ({self.quantity} units) by {self.user.username}"

class OrderStatusHistory(models.Model):
    """Track order status changes"""
    order = models.ForeignKey(OrderQueue, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order.id} - {self.status} at {self.created_at}"
