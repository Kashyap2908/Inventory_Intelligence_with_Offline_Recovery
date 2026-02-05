#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_inventory.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import UserProfile

print("🔧 DEBUG: Checking all users in the system...")
print("=" * 50)

users = User.objects.all()
print(f"Total users: {users.count()}")
print()

for user in users:
    try:
        profile = user.userprofile
        print(f"- {user.username} (ID: {user.id}) - Role: {profile.role}")
    except UserProfile.DoesNotExist:
        print(f"- {user.username} (ID: {user.id}) - No profile")

print()
print("Inventory users specifically:")
inventory_users = UserProfile.objects.filter(role='inventory')
print(f"Total inventory users: {inventory_users.count()}")

for profile in inventory_users:
    print(f"- {profile.user.username} (ID: {profile.user.id})")