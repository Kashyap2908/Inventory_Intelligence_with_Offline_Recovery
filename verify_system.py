#!/usr/bin/env python
"""
NeuroStock System Verification Script
Run this to verify all components are working correctly
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import (
    Product, ExpiryStock, OrderQueue, SalesBill, 
    UserProfile, Notification, LowStockThreshold, 
    StockMovement, OrderStatusHistory
)

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    print(f"✅ {text}")

def print_error(text):
    print(f"❌ {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def verify_models():
    """Verify all models are accessible"""
    print_header("VERIFYING DATABASE MODELS")
    
    models = [
        ('User', User),
        ('UserProfile', UserProfile),
        ('Product', Product),
        ('ExpiryStock', ExpiryStock),
        ('OrderQueue', OrderQueue),
        ('SalesBill', SalesBill),
        ('Notification', Notification),
        ('LowStockThreshold', LowStockThreshold),
        ('StockMovement', StockMovement),
        ('OrderStatusHistory', OrderStatusHistory),
    ]
    
    for name, model in models:
        try:
            count = model.objects.count()
            print_success(f"{name}: {count} records")
        except Exception as e:
            print_error(f"{name}: Error - {str(e)}")

def verify_users():
    """Verify user setup"""
    print_header("VERIFYING USERS")
    
    users = User.objects.all()
    print_info(f"Total Users: {users.count()}")
    
    for user in users:
        try:
            profile = user.userprofile
            print_success(f"{user.username} - Role: {profile.role}")
        except UserProfile.DoesNotExist:
            print_error(f"{user.username} - No profile!")

def verify_products():
    """Verify products"""
    print_header("VERIFYING PRODUCTS")
    
    products = Product.objects.all()
    print_info(f"Total Products: {products.count()}")
    
    for product in products:
        total_stock = product.total_stock
        print_success(f"{product.name} - Stock: {total_stock} units")

def verify_stock_distribution():
    """Verify stock distribution by user"""
    print_header("VERIFYING STOCK DISTRIBUTION")
    
    products = Product.objects.all()
    
    for product in products:
        print_info(f"\n{product.name}:")
        stock_by_user = product.get_all_users_stock()
        
        if stock_by_user:
            for user_stock in stock_by_user:
                username = user_stock['user__username']
                first_name = user_stock['user__first_name'] or username
                total = user_stock['total']
                print_success(f"  {first_name}: {total} units")
        else:
            print_info("  No stock assigned to users")

def verify_features():
    """Verify key features"""
    print_header("VERIFYING KEY FEATURES")
    
    # Check if ExpiryStock has user field
    try:
        stock = ExpiryStock.objects.first()
        if stock:
            if hasattr(stock, 'user'):
                print_success("User-specific stock tracking: Enabled")
            else:
                print_error("User-specific stock tracking: Missing user field")
        else:
            print_info("No stock entries to verify")
    except Exception as e:
        print_error(f"Stock verification error: {str(e)}")
    
    # Check OrderQueue enhancements
    try:
        order = OrderQueue.objects.first()
        if order:
            if hasattr(order, 'fulfilled_quantity'):
                print_success("Partial fulfillment: Enabled")
            else:
                print_error("Partial fulfillment: Missing fields")
        else:
            print_info("No orders to verify")
    except Exception as e:
        print_error(f"Order verification error: {str(e)}")
    
    # Check new models
    try:
        LowStockThreshold.objects.count()
        print_success("Low Stock Alerts: Model exists")
    except Exception as e:
        print_error(f"Low Stock Alerts: {str(e)}")
    
    try:
        StockMovement.objects.count()
        print_success("Audit Trail: Model exists")
    except Exception as e:
        print_error(f"Audit Trail: {str(e)}")
    
    try:
        OrderStatusHistory.objects.count()
        print_success("Order Status Tracking: Model exists")
    except Exception as e:
        print_error(f"Order Status Tracking: {str(e)}")

def verify_admin_user():
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
                print_error(f"Admin has wrong role: {profile.role}")
        except UserProfile.DoesNotExist:
            print_error("Admin user has no profile!")
    except User.DoesNotExist:
        print_error("Admin user not found!")
        print_info("Create admin user with: python manage.py createsuperuser")

def main():
    """Main verification function"""
    print("\n" + "🔍 "*20)
    print("  NEUROSTOCK SYSTEM VERIFICATION")
    print("🔍 "*20)
    
    try:
        verify_models()
        verify_users()
        verify_products()
        verify_stock_distribution()
        verify_features()
        verify_admin_user()
        
        print_header("VERIFICATION COMPLETE")
        print_success("System verification completed!")
        print_info("Check above for any errors or warnings")
        
    except Exception as e:
        print_error(f"Verification failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
