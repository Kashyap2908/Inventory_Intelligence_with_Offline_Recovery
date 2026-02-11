import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import Product, ExpiryStock, UserProfile
from datetime import date, timedelta
import random

print("🏪 Adding Stock to Inventory Stores...")
print("=" * 60)

# Get all inventory users
inventory_users = User.objects.filter(userprofile__role='inventory')

if not inventory_users.exists():
    print("❌ No inventory users found!")
    exit()

print(f"Found {inventory_users.count()} inventory stores:")
for user in inventory_users:
    print(f"  - {user.userprofile.full_identity}")

print("\n📦 Adding realistic stock to each store...")

# Get all products
products = Product.objects.all()

# Define stock ranges based on ABC classification
def get_stock_range(trend_score):
    """Return realistic stock range based on product demand"""
    if trend_score >= 7.0:  # A products - High demand
        return (30, 80)  # Higher stock for fast-moving items
    elif trend_score >= 4.0:  # B products - Medium demand
        return (15, 50)  # Moderate stock
    else:  # C products - Low demand
        return (5, 30)  # Lower stock for slow-moving items

total_added = 0

for user in inventory_users:
    print(f"\n🏪 {user.userprofile.full_identity}:")
    user_stock_count = 0
    
    # Add stock for random selection of products (not all products in each store)
    # Each store will have 60-70% of all products
    num_products_in_store = int(products.count() * random.uniform(0.6, 0.7))
    selected_products = random.sample(list(products), num_products_in_store)
    
    for product in selected_products:
        # Check if this user already has stock for this product
        existing_stock = ExpiryStock.objects.filter(
            product=product,
            user=user
        ).exists()
        
        if not existing_stock:
            # Get stock range based on product demand
            min_stock, max_stock = get_stock_range(product.trend_score)
            quantity = random.randint(min_stock, max_stock)
            
            # Set expiry date (3-12 months from now)
            days_to_expiry = random.randint(90, 365)
            expiry_date = date.today() + timedelta(days=days_to_expiry)
            
            # Create stock entry
            ExpiryStock.objects.create(
                product=product,
                quantity=quantity,
                expiry_date=expiry_date,
                user=user
            )
            
            user_stock_count += 1
            total_added += 1
    
    # Calculate total units for this user
    total_units = sum(
        stock.quantity for stock in ExpiryStock.objects.filter(user=user)
    )
    print(f"  ✅ Added stock for {user_stock_count} products")
    print(f"  📊 Total units in store: {total_units}")

print("\n" + "=" * 60)
print("🎉 Inventory Stock Added Successfully!")
print("=" * 60)

# Show summary for each store
print("\n📊 Store-wise Summary:")
for user in inventory_users:
    stock_entries = ExpiryStock.objects.filter(user=user)
    total_units = sum(stock.quantity for stock in stock_entries)
    product_count = stock_entries.values('product').distinct().count()
    
    print(f"\n🏪 {user.userprofile.full_identity}:")
    print(f"  - Products: {product_count}")
    print(f"  - Total Units: {total_units}")
    print(f"  - Stock Entries: {stock_entries.count()}")

print("\n💡 All inventory stores now have realistic stock!")
print("💡 Login as inventory user to see 'My Stock' column filled!")
