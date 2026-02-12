"""
Add sample shop owners for testing
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from inventory.models import ShopOwner

def add_sample_shop_owners():
    print("Adding sample shop owners...")
    
    shop_owners_data = [
        {
            'name': 'Rajesh Kumar',
            'shop_name': 'Kumar General Store',
            'phone_number': '9876543210',
            'email': 'rajesh@kumarstore.com',
            'address': '123 Main Street, Mumbai, Maharashtra'
        },
        {
            'name': 'Priya Sharma',
            'shop_name': 'Sharma Supermarket',
            'phone_number': '9876543211',
            'email': 'priya@sharmamarket.com',
            'address': '456 Market Road, Delhi'
        },
        {
            'name': 'Amit Patel',
            'shop_name': 'Patel Provisions',
            'phone_number': '9876543212',
            'email': 'amit@patelprovisions.com',
            'address': '789 Gandhi Nagar, Ahmedabad, Gujarat'
        },
        {
            'name': 'Sunita Reddy',
            'shop_name': 'Reddy Retail',
            'phone_number': '9876543213',
            'email': 'sunita@reddyretail.com',
            'address': '321 MG Road, Bangalore, Karnataka'
        },
        {
            'name': 'Vikram Singh',
            'shop_name': 'Singh Stores',
            'phone_number': '9876543214',
            'email': 'vikram@singhstores.com',
            'address': '654 Station Road, Jaipur, Rajasthan'
        },
    ]
    
    for data in shop_owners_data:
        shop_owner, created = ShopOwner.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        
        if created:
            print(f"✓ Added: {shop_owner.name} - {shop_owner.shop_name}")
        else:
            print(f"- Already exists: {shop_owner.name}")
    
    print(f"\nTotal shop owners: {ShopOwner.objects.count()}")
    print("\n✅ Sample shop owners added successfully!")
    print("\nNext steps:")
    print("1. Go to http://127.0.0.1:8000/manage-shop-owners/")
    print("2. Upload CSV files for shop owners")
    print("3. Go to Billing page and select shop owner to process orders")

if __name__ == '__main__':
    add_sample_shop_owners()
