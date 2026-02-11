import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from inventory.models import Product

print("📊 Setting Realistic Trend Scores for ABC Analysis...")
print("=" * 60)

# Define realistic trend scores based on product demand patterns
# A products (7-10): High demand, fast-moving
# B products (4-6.9): Medium demand
# C products (0-3.9): Low demand, slow-moving

trend_scores = {
    # A Products - High Demand (7-10)
    "Milk 1L": 9.2,
    "Bread Loaf": 8.8,
    "Eggs (12 pcs)": 8.5,
    "Sugar 1kg": 8.3,
    "Cooking Oil 1L": 8.1,
    "Tea Packets 250g": 7.9,
    "Biscuits Pack": 7.7,
    "Instant Noodles": 7.5,
    "Chips 100g": 7.3,
    "Soft Drinks 2L": 7.2,
    "Basmati Rice 5kg": 7.1,
    "Wheat Flour 10kg": 7.0,
    
    # B Products - Medium Demand (4-6.9)
    "Butter 500g": 6.8,
    "Toothpaste": 6.5,
    "Shampoo 200ml": 6.3,
    "Detergent Powder 1kg": 6.1,
    "Soap (3 pcs)": 5.9,
    "Salt 1kg": 5.7,
    "Curd 500g": 5.5,
    "Cookies Pack": 5.3,
    "Fruit Juices 1L": 5.1,
    "Dishwash Liquid 500ml": 4.9,
    "Pasta 500g": 4.7,
    "Namkeen 200g": 4.5,
    "Wafers 100g": 4.3,
    "Coffee Packs 200g": 4.1,
    "Handwash 200ml": 4.0,
    
    # C Products - Low Demand (0-3.9)
    "Paneer 200g": 3.8,
    "Cheese Slice": 3.6,
    "Ghee 500ml": 3.4,
    "Breakfast Cereals": 3.2,
    "Oats 1kg": 3.0,
    "Peanut Butter": 2.8,
    "Energy Drinks": 2.6,
    "Body Lotion": 2.4,
    "Hair Oil 200ml": 2.2,
    "Face Wash": 2.0,
    "Detergent Liquid 1L": 1.8,
    "Floor Cleaner 1L": 1.6,
    "Toilet Cleaner 500ml": 1.4,
    "Phenyl 1L": 1.2,
    "Garbage Bags (30 pcs)": 1.0,
    "Turmeric Powder": 3.9,
    "Red Chili Powder": 3.7,
    "Coriander Powder": 3.5,
    "Bun (6 pcs)": 3.3,
    "Pav (6 pcs)": 3.1,
    "Eggs (30 pcs)": 2.9,
    "Chocolates": 6.9,
    "Flavored Milk": 5.8,
    "Buttermilk (Packaged)": 4.2,
    "Popcorn 100g": 4.4,
    "Salted Peanuts 200g": 4.6,
    "Nachos 150g": 3.2,
}

updated_count = 0
a_count = 0
b_count = 0
c_count = 0

for product_name, score in trend_scores.items():
    try:
        product = Product.objects.get(name=product_name)
        product.trend_score = score
        product.save()
        
        # Determine ABC class
        if score >= 7.0:
            abc_class = "A"
            a_count += 1
        elif score >= 4.0:
            abc_class = "B"
            b_count += 1
        else:
            abc_class = "C"
            c_count += 1
        
        updated_count += 1
        print(f"  ✅ {product_name}: {score}/10 → Class {abc_class}")
        
    except Product.DoesNotExist:
        print(f"  ⚠️ Product not found: {product_name}")

# Set default scores for remaining products
remaining_products = Product.objects.exclude(name__in=trend_scores.keys())
for product in remaining_products:
    product.trend_score = 3.0  # Default C class
    product.save()
    c_count += 1
    print(f"  ✅ {product.name}: 3.0/10 → Class C (default)")

print("\n" + "=" * 60)
print("🎉 Trend Scores Updated Successfully!")
print("=" * 60)
print(f"\n📊 ABC Distribution:")
print(f"  🔴 A Products (High Demand): {a_count} products")
print(f"  🟡 B Products (Medium Demand): {b_count} products")
print(f"  ⚪ C Products (Low Demand): {c_count} products")
print(f"\n  Total Updated: {updated_count + len(remaining_products)} products")
print("\n💡 ABC Analysis is now realistic and varied!")
print("💡 Check Admin Dashboard → Stock Intelligence to see color-coded ABC classes!")
