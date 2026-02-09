#!/usr/bin/env python
"""
Reset Database with Clean Demo Data
- Remove old products and users
- Create 3 inventory users with stores
- Create 10 essential products (with expiry dates)
- Add sample stock for testing
"""

import os
import sys
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import (
    Product, ExpiryStock, OrderQueue, SalesBill, SalesBillItem,
    UserProfile, Notification, LowStockThreshold, 
    StockMovement, OrderStatusHistory
)

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"✅ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def cleanup_database():
    """Remove old data except admin user"""
    print_header("CLEANING DATABASE")
    
    # Delete all notifications
    count = Notification.objects.all().delete()[0]
    print_success(f"Deleted {count} notifications")
    
    # Delete all orders
    count = OrderQueue.objects.all().delete()[0]
    print_success(f"Deleted {count} orders")
    
    # Delete all bills
    count = SalesBill.objects.all().delete()[0]
    print_success(f"Deleted {count} bills")
    
    # Delete all stock
    count = ExpiryStock.objects.all().delete()[0]
    print_success(f"Deleted {count} stock entries")
    
    # Delete all products
    count = Product.objects.all().delete()[0]
    print_success(f"Deleted {count} products")
    
    # Delete non-admin users
    non_admin_users = User.objects.exclude(username='admin')
    count = non_admin_users.count()
    non_admin_users.delete()
    print_success(f"Deleted {count} non-admin users")
    
    print_info("Database cleaned!")

def create_demo_users():
    """Create 3 inventory users with store information"""
    print_header("CREATING DEMO USERS")
    
    users_data = [
        {
            'username': 'mumbai_store',
            'email': 'mumbai@neurostock.com',
            'password': 'mumbai123',
            'first_name': 'Raj',
            'last_name': 'Sharma',
            'store_name': 'Mumbai Store',
            'store_location': 'Andheri West, Mumbai, Maharashtra'
        },
        {
            'username': 'delhi_store',
            'email': 'delhi@neurostock.com',
            'password': 'delhi123',
            'first_name': 'Priya',
            'last_name': 'Singh',
            'store_name': 'Delhi Store',
            'store_location': 'Connaught Place, New Delhi'
        },
        {
            'username': 'bangalore_store',
            'email': 'bangalore@neurostock.com',
            'password': 'bangalore123',
            'first_name': 'Amit',
            'last_name': 'Kumar',
            'store_name': 'Bangalore Store',
            'store_location': 'Koramangala, Bangalore, Karnataka'
        }
    ]
    
    created_users = []
    for user_data in users_data:
        # Create user
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        
        # Create profile with store info
        UserProfile.objects.create(
            user=user,
            role='inventory',
            store_name=user_data['store_name'],
            store_location=user_data['store_location']
        )
        
        created_users.append(user)
        print_success(f"Created: {user_data['first_name']} {user_data['last_name']} ({user_data['store_name']})")
    
    return created_users

def create_demo_products():
    """Create 10 essential products with expiry dates"""
    print_header("CREATING DEMO PRODUCTS")
    
    products_data = [
        {'name': 'Basmati Rice 5kg', 'category': 'Groceries', 'cost': 250, 'selling': 350},
        {'name': 'Wheat Flour 10kg', 'category': 'Groceries', 'cost': 300, 'selling': 400},
        {'name': 'Sugar 1kg', 'category': 'Groceries', 'cost': 40, 'selling': 50},
        {'name': 'Cooking Oil 1L', 'category': 'Groceries', 'cost': 120, 'selling': 150},
        {'name': 'Milk 1L', 'category': 'Dairy', 'cost': 50, 'selling': 60},
        {'name': 'Butter 500g', 'category': 'Dairy', 'cost': 200, 'selling': 250},
        {'name': 'Bread Loaf', 'category': 'Bakery', 'cost': 30, 'selling': 40},
        {'name': 'Eggs (12 pcs)', 'category': 'Dairy', 'cost': 60, 'selling': 80},
        {'name': 'Biscuits Pack', 'category': 'Snacks', 'cost': 20, 'selling': 30},
        {'name': 'Instant Noodles', 'category': 'Snacks', 'cost': 12, 'selling': 20},
    ]
    
    created_products = []
    for product_data in products_data:
        product = Product.objects.create(
            name=product_data['name'],
            category=product_data['category'],
            cost_price=product_data['cost'],
            selling_price=product_data['selling'],
            new_price=product_data['selling'],
            abc_classification='B',
            trend_score=5.0
        )
        created_products.append(product)
        print_success(f"Created: {product.name} (₹{product.cost_price}/₹{product.selling_price})")
    
    return created_products

def add_demo_stock(users, products):
    """Add sample stock for each user"""
    print_header("ADDING DEMO STOCK")
    
    today = date.today()
    
    # Mumbai Store - First 4 products
    mumbai_user = users[0]
    for i, product in enumerate(products[:4]):
        quantity = 50 + (i * 10)
        expiry = today + timedelta(days=180 + (i * 30))
        
        ExpiryStock.objects.create(
            product=product,
            quantity=quantity,
            expiry_date=expiry,
            user=mumbai_user
        )
        print_success(f"Mumbai: {product.name} - {quantity} units (Expires: {expiry})")
    
    # Delhi Store - Products 3-7
    delhi_user = users[1]
    for i, product in enumerate(products[3:7]):
        quantity = 40 + (i * 15)
        expiry = today + timedelta(days=150 + (i * 30))
        
        ExpiryStock.objects.create(
            product=product,
            quantity=quantity,
            expiry_date=expiry,
            user=delhi_user
        )
        print_success(f"Delhi: {product.name} - {quantity} units (Expires: {expiry})")
    
    # Bangalore Store - Last 4 products
    bangalore_user = users[2]
    for i, product in enumerate(products[6:10]):
        quantity = 60 + (i * 10)
        expiry = today + timedelta(days=120 + (i * 30))
        
        ExpiryStock.objects.create(
            product=product,
            quantity=quantity,
            expiry_date=expiry,
            user=bangalore_user
        )
        print_success(f"Bangalore: {product.name} - {quantity} units (Expires: {expiry})")

def verify_admin():
    """Verify admin user exists"""
    print_header("VERIFYING ADMIN USER")
    
    try:
        admin = User.objects.get(username='admin')
        print_success(f"Admin user exists: {admin.username}")
        
        try:
            profile = admin.userprofile
            if profile.role == 'admin':
                print_success("Admin role correctly assigned")
            else:
                profile.role = 'admin'
                profile.save()
                print_success("Admin role updated")
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=admin, role='admin')
            print_success("Admin profile created")
    except User.DoesNotExist:
        print_info("Admin user not found. Creating...")
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@neurostock.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        UserProfile.objects.create(user=admin, role='admin')
        print_success("Admin user created (username: admin, password: admin123)")

def print_summary():
    """Print final summary"""
    print_header("DEMO DATA SUMMARY")
    
    print_info(f"Total Users: {User.objects.count()}")
    print_info(f"  - Admin: 1")
    print_info(f"  - Inventory: {UserProfile.objects.filter(role='inventory').count()}")
    
    print_info(f"\nTotal Products: {Product.objects.count()}")
    
    print_info(f"\nTotal Stock Entries: {ExpiryStock.objects.count()}")
    
    print("\n" + "="*60)
    print("  LOGIN CREDENTIALS")
    print("="*60)
    print("\n🔐 Admin:")
    print("   Username: admin")
    print("   Password: admin123")
    
    print("\n🏪 Mumbai Store:")
    print("   Username: mumbai_store")
    print("   Password: mumbai123")
    
    print("\n🏪 Delhi Store:")
    print("   Username: delhi_store")
    print("   Password: delhi123")
    
    print("\n🏪 Bangalore Store:")
    print("   Username: bangalore_store")
    print("   Password: bangalore123")
    
    print("\n" + "="*60)
    print("  ✅ DEMO DATA READY!")
    print("="*60)
    print("\n🌐 Access: http://127.0.0.1:8000/")
    print("\n")

def main():
    """Main function"""
    print("\n" + "🔄 "*20)
    print("  NEUROSTOCK - RESET TO DEMO DATA")
    print("🔄 "*20)
    
    try:
        # Step 1: Cleanup
        cleanup_database()
        
        # Step 2: Verify/Create Admin
        verify_admin()
        
        # Step 3: Create Demo Users
        users = create_demo_users()
        
        # Step 4: Create Products
        products = create_demo_products()
        
        # Step 5: Add Stock
        add_demo_stock(users, products)
        
        # Step 6: Summary
        print_summary()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
