import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import UserProfile, Product, ExpiryStock
from datetime import date, timedelta

print("🏢 Setting up Company Stock System...")
print("=" * 50)

# Create or get Company user for admin's stock
try:
    company_user = User.objects.get(username='company_stock')
    print("✅ Company stock user already exists")
except User.DoesNotExist:
    company_user = User.objects.create_user(
        username='company_stock',
        password='company_internal_use_only',
        first_name='Company',
        last_name='Warehouse'
    )
    
    # Create profile for company user
    UserProfile.objects.create(
        user=company_user,
        role='admin',
        store_name='Company Warehouse',
        store_location='Main Distribution Center',
        phone_number='0000000000'
    )
    print("✅ Created company stock user")

# Transfer all unassigned stock to company
unassigned_stock = ExpiryStock.objects.filter(user__isnull=True)
count = unassigned_stock.count()
if count > 0:
    unassigned_stock.update(user=company_user)
    print(f"✅ Transferred {count} unassigned stock entries to company")

# Add initial company stock for all products
products = Product.objects.all()
print(f"\n📦 Adding company stock for {products.count()} products...")

for product in products:
    # Check if company already has stock for this product
    existing_stock = ExpiryStock.objects.filter(
        product=product,
        user=company_user
    ).exists()
    
    if not existing_stock:
        # Add company stock (100-500 units per product)
        quantity = 200  # Default company stock
        expiry_date = date.today() + timedelta(days=365)  # 1 year expiry
        
        ExpiryStock.objects.create(
            product=product,
            quantity=quantity,
            expiry_date=expiry_date,
            user=company_user
        )
        print(f"  ✅ Added {quantity} units of {product.name} to company stock")

print("\n" + "=" * 50)
print("🎉 Company Stock System Setup Complete!")
print("=" * 50)
print("\n📊 Summary:")
print(f"  - Company User: {company_user.username}")
print(f"  - Company Stock Entries: {ExpiryStock.objects.filter(user=company_user).count()}")
print(f"  - Total Company Stock: {sum(s.quantity for s in ExpiryStock.objects.filter(user=company_user))}")
print("\n💡 Admin can now manage company stock separately!")
print("💡 When admin approves requests, stock will be deducted from company warehouse!")
