import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import Product, ExpiryStock
from datetime import date, timedelta

print("📦 Adding Products with Different Expiry Dates...")
print("=" * 60)

# Get company_stock user (or create if doesn't exist)
try:
    company_user = User.objects.get(username='company_stock')
    print(f"✅ Using company_stock user")
except User.DoesNotExist:
    print("❌ company_stock user not found. Please run setup_company_stock.py first!")
    exit()

# Define products with various expiry scenarios
products_with_expiry = [
    # (name, category, cost, selling, quantity, days_until_expiry)
    
    # Already expired (for testing)
    ("Expired Milk 1L", "Dairy", 50, 60, 20, -5),
    ("Expired Bread", "Bakery", 30, 40, 15, -2),
    
    # Expiring very soon (1-7 days)
    ("Fresh Milk 1L", "Dairy", 50, 60, 50, 3),
    ("Fresh Curd 500g", "Dairy", 40, 50, 30, 2),
    ("Fresh Paneer 200g", "Dairy", 80, 100, 25, 4),
    ("Fresh Bread Loaf", "Bakery", 30, 40, 40, 1),
    
    # Expiring soon (1-2 weeks)
    ("Butter 500g", "Dairy", 200, 250, 35, 10),
    ("Cheese Slice", "Dairy", 150, 180, 20, 14),
    ("Bun (6 pcs)", "Bakery", 25, 35, 30, 7),
    
    # Expiring in 1 month
    ("Eggs (12 pcs)", "Dairy", 60, 80, 100, 30),
    ("Flavored Milk", "Beverages", 30, 40, 60, 25),
    ("Buttermilk (Packaged)", "Beverages", 25, 35, 40, 28),
    
    # Expiring in 2-3 months
    ("Instant Noodles", "Packaged Foods", 12, 20, 200, 60),
    ("Biscuits Pack", "Packaged Foods", 20, 30, 150, 75),
    ("Chips 100g", "Snacks", 20, 30, 120, 90),
    
    # Expiring in 6 months
    ("Pasta 500g", "Packaged Foods", 60, 80, 80, 180),
    ("Breakfast Cereals", "Packaged Foods", 200, 280, 50, 170),
    ("Oats 1kg", "Packaged Foods", 150, 200, 60, 185),
    
    # Long shelf life (1 year+)
    ("Basmati Rice 5kg", "Groceries", 250, 350, 200, 365),
    ("Wheat Flour 10kg", "Groceries", 300, 400, 150, 400),
    ("Sugar 1kg", "Groceries", 40, 50, 300, 500),
    ("Cooking Oil 1L", "Groceries", 120, 150, 100, 450),
    ("Salt 1kg", "Groceries", 20, 25, 250, 730),
]

added_products = 0
added_stock = 0

for name, category, cost, selling, quantity, days_offset in products_with_expiry:
    # Create or get product
    product, created = Product.objects.get_or_create(
        name=name,
        defaults={
            'category': category,
            'cost_price': cost,
            'selling_price': selling,
            'new_price': selling,
            'abc_classification': 'C',
            'trend_score': 5.0,
            'discount_percentage': 0.0
        }
    )
    
    if created:
        added_products += 1
        print(f"  ✅ Added product: {name}")
    
    # Calculate expiry date
    expiry_date = date.today() + timedelta(days=days_offset)
    
    # Add stock with specific expiry date
    stock, stock_created = ExpiryStock.objects.get_or_create(
        product=product,
        user=company_user,
        expiry_date=expiry_date,
        defaults={'quantity': quantity}
    )
    
    if stock_created:
        added_stock += 1
        status = "EXPIRED" if days_offset < 0 else f"{days_offset} days"
        print(f"     📦 Stock: {quantity} units, Expires: {expiry_date} ({status})")
    else:
        # Update quantity if stock entry already exists
        stock.quantity += quantity
        stock.save()
        print(f"     🔄 Updated stock: +{quantity} units (Total: {stock.quantity})")

print("\n" + "=" * 60)
print("🎉 Products with Expiry Dates Added Successfully!")
print("=" * 60)
print(f"\n📊 Summary:")
print(f"  - New Products: {added_products}")
print(f"  - Stock Entries: {added_stock}")
print(f"  - Total Products: {Product.objects.count()}")

# Show expiry summary
print("\n📅 Expiry Summary:")
expired = ExpiryStock.objects.filter(
    user=company_user,
    expiry_date__lt=date.today()
).count()
expiring_soon = ExpiryStock.objects.filter(
    user=company_user,
    expiry_date__gte=date.today(),
    expiry_date__lte=date.today() + timedelta(days=7)
).count()
expiring_month = ExpiryStock.objects.filter(
    user=company_user,
    expiry_date__gt=date.today() + timedelta(days=7),
    expiry_date__lte=date.today() + timedelta(days=30)
).count()

print(f"  - Already Expired: {expired}")
print(f"  - Expiring in 7 days: {expiring_soon}")
print(f"  - Expiring in 30 days: {expiring_month}")

print("\n💡 Run the Django server and check the inventory dashboard!")
print("💡 You should see expiry warnings for products expiring soon.")
