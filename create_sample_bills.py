import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import Product, SalesBill, SalesBillItem
from datetime import datetime, timedelta
from decimal import Decimal

print("🧾 Creating sample bills for testing...")

# Get inventory users
inventory_users = User.objects.filter(userprofile__role='inventory')
products = Product.objects.all()[:5]  # Get first 5 products

if not inventory_users.exists():
    print("❌ No inventory users found!")
    exit()

if not products.exists():
    print("❌ No products found!")
    exit()

# Create bills for the last 7 days
bills_created = 0
for days_ago in range(7):
    date = datetime.now() - timedelta(days=days_ago)
    
    # Create 2-3 bills per day for different stores
    for user in inventory_users[:2]:  # Use first 2 inventory users
        # Create bill
        bill_number = f"BILL-{date.strftime('%Y%m%d')}-{user.id}-{bills_created}"
        
        bill = SalesBill.objects.create(
            bill_number=bill_number,
            created_by=user,
            total_amount=0
        )
        
        # Manually set created_at to past date
        bill.created_at = date
        
        # Add 2-3 random items to bill
        total = Decimal('0')
        for product in products[:2]:
            quantity = 10 + (bills_created % 20)
            item_total = product.selling_price * quantity
            
            SalesBillItem.objects.create(
                bill=bill,
                product=product,
                quantity=quantity,
                price=product.selling_price,
                total=item_total
            )
            
            total += item_total
        
        # Update bill total
        bill.total_amount = total
        bill.save()
        
        bills_created += 1
        print(f"✅ Created bill {bill_number} for {user.userprofile.full_identity} - ₹{total}")

print(f"\n🎉 Successfully created {bills_created} sample bills!")
print(f"📊 Bills span across last 7 days")
print(f"🏪 Bills distributed across {inventory_users.count()} stores")
