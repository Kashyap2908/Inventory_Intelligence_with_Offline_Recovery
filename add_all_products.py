import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from inventory.models import Product
from datetime import date, timedelta

print("🛒 Adding Complete Product Catalog...")
print("=" * 60)

# Complete product list with categories
products_data = [
    # Groceries
    ("Basmati Rice 5kg", "Groceries", 250, 350),
    ("Wheat Flour 10kg", "Groceries", 300, 400),
    ("Sugar 1kg", "Groceries", 40, 50),
    ("Cooking Oil 1L", "Groceries", 120, 150),
    ("Salt 1kg", "Groceries", 20, 25),
    ("Turmeric Powder", "Groceries", 80, 100),
    ("Red Chili Powder", "Groceries", 90, 110),
    ("Coriander Powder", "Groceries", 70, 90),
    
    # Dairy Products
    ("Milk 1L", "Dairy", 50, 60),
    ("Butter 500g", "Dairy", 200, 250),
    ("Cheese Slice", "Dairy", 150, 180),
    ("Paneer 200g", "Dairy", 80, 100),
    ("Curd 500g", "Dairy", 40, 50),
    ("Ghee 500ml", "Dairy", 300, 380),
    
    # Bakery
    ("Bread Loaf", "Bakery", 30, 40),
    ("Bun (6 pcs)", "Bakery", 25, 35),
    ("Pav (6 pcs)", "Bakery", 20, 30),
    
    # Eggs
    ("Eggs (12 pcs)", "Dairy", 60, 80),
    ("Eggs (30 pcs)", "Dairy", 140, 180),
    
    # Packaged Foods
    ("Biscuits Pack", "Packaged Foods", 20, 30),
    ("Instant Noodles", "Packaged Foods", 12, 20),
    ("Pasta 500g", "Packaged Foods", 60, 80),
    ("Breakfast Cereals", "Packaged Foods", 200, 280),
    ("Chocolates", "Packaged Foods", 10, 15),
    ("Namkeen 200g", "Packaged Foods", 40, 55),
    ("Oats 1kg", "Packaged Foods", 150, 200),
    ("Peanut Butter", "Packaged Foods", 180, 240),
    
    # Beverages
    ("Soft Drinks 2L", "Beverages", 60, 80),
    ("Fruit Juices 1L", "Beverages", 80, 110),
    ("Energy Drinks", "Beverages", 90, 120),
    ("Tea Packets 250g", "Beverages", 120, 160),
    ("Coffee Packs 200g", "Beverages", 200, 280),
    ("Flavored Milk", "Beverages", 30, 40),
    ("Buttermilk (Packaged)", "Beverages", 25, 35),
    
    # Personal Care
    ("Shampoo 200ml", "Personal Care", 150, 200),
    ("Soap (3 pcs)", "Personal Care", 60, 80),
    ("Toothpaste", "Personal Care", 80, 110),
    ("Face Wash", "Personal Care", 120, 160),
    ("Hair Oil 200ml", "Personal Care", 100, 140),
    ("Body Lotion", "Personal Care", 180, 240),
    ("Handwash 200ml", "Personal Care", 90, 120),
    
    # Household Essentials
    ("Detergent Powder 1kg", "Household", 120, 160),
    ("Detergent Liquid 1L", "Household", 180, 240),
    ("Dishwash Liquid 500ml", "Household", 90, 120),
    ("Floor Cleaner 1L", "Household", 100, 140),
    ("Toilet Cleaner 500ml", "Household", 80, 110),
    ("Garbage Bags (30 pcs)", "Household", 60, 80),
    ("Phenyl 1L", "Household", 50, 70),
    
    # Snacks
    ("Chips 100g", "Snacks", 20, 30),
    ("Popcorn 100g", "Snacks", 40, 55),
    ("Salted Peanuts 200g", "Snacks", 60, 80),
    ("Nachos 150g", "Snacks", 50, 70),
    ("Cookies Pack", "Snacks", 30, 45),
    ("Wafers 100g", "Snacks", 20, 30),
]

added_count = 0
updated_count = 0

for name, category, cost, selling in products_data:
    # Check if product already exists
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
        added_count += 1
        print(f"  ✅ Added: {name} ({category}) - ₹{cost}/₹{selling}")
    else:
        # Update existing product
        product.category = category
        product.cost_price = cost
        product.selling_price = selling
        product.new_price = selling
        product.save()
        updated_count += 1
        print(f"  🔄 Updated: {name}")

print("\n" + "=" * 60)
print("🎉 Product Catalog Setup Complete!")
print("=" * 60)
print(f"\n📊 Summary:")
print(f"  - New Products Added: {added_count}")
print(f"  - Existing Products Updated: {updated_count}")
print(f"  - Total Products: {Product.objects.count()}")
print("\n💡 Next step: Run setup_company_stock.py to add company stock!")
