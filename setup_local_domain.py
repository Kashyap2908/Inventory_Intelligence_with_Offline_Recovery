#!/usr/bin/env python
"""
NeuroStock AI - Local Professional Domain Setup
Setup professional domain names for local network access
"""

import os
import sys
import subprocess
import platform

def print_header():
    print("🧠 NeuroStock AI - Local Professional Domain Setup")
    print("=" * 60)
    print("Transform IP address to professional local domain!")
    print("=" * 60)

def get_system_info():
    """Get system information"""
    system = platform.system().lower()
    print(f"🖥️ Detected System: {platform.system()}")
    return system

def setup_windows_hosts():
    """Setup Windows hosts file"""
    hosts_file = r"C:\Windows\System32\drivers\etc\hosts"
    
    # Professional domain entries
    entries = [
        "# NeuroStock AI Professional Local Domains",
        "10.55.157.192    neurostock.local",
        "10.55.157.192    neurostock-ai.local", 
        "10.55.157.192    inventory.neurostock",
        "10.55.157.192    smart-inventory.local",
        "10.55.157.192    neuroinventory.local",
        "10.55.157.192    ns.local",
        "10.55.157.192    neuro.local",
        "10.55.157.192    stock.local",
        "10.55.157.192    ai.local",
        ""
    ]
    
    print("📝 Windows Hosts File Setup:")
    print("=" * 40)
    print("1. Open Command Prompt as Administrator")
    print("2. Run: notepad C:\\Windows\\System32\\drivers\\etc\\hosts")
    print("3. Add these lines at the end:")
    print()
    
    for entry in entries:
        print(f"   {entry}")
    
    # Save to file for easy copying
    with open("hosts_entries.txt", "w") as f:
        f.write("\n".join(entries))
    
    print(f"\n✅ Entries saved to: hosts_entries.txt")
    print(f"📋 Copy and paste from this file to your hosts file")

def setup_linux_mac_hosts():
    """Setup Linux/Mac hosts file"""
    hosts_file = "/etc/hosts"
    
    entries = [
        "# NeuroStock AI Professional Local Domains",
        "10.55.157.192    neurostock.local",
        "10.55.157.192    neurostock-ai.local",
        "10.55.157.192    inventory.neurostock", 
        "10.55.157.192    smart-inventory.local",
        "10.55.157.192    neuroinventory.local",
        "10.55.157.192    ns.local",
        "10.55.157.192    neuro.local",
        "10.55.157.192    stock.local",
        "10.55.157.192    ai.local",
        ""
    ]
    
    print("📝 Linux/Mac Hosts File Setup:")
    print("=" * 40)
    print("Run this command:")
    print()
    print("sudo nano /etc/hosts")
    print()
    print("Add these lines at the end:")
    print()
    
    for entry in entries:
        print(f"   {entry}")
    
    # Save to file
    with open("hosts_entries.txt", "w") as f:
        f.write("\n".join(entries))
    
    print(f"\n✅ Entries saved to: hosts_entries.txt")

def update_django_settings():
    """Update Django settings for professional domains"""
    settings_update = '''
# Add to ALLOWED_HOSTS in smart_inventory/settings.py
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1', 
    '10.55.157.192',
    'neurostock.local',
    'neurostock-ai.local',
    'inventory.neurostock',
    'smart-inventory.local',
    'neuroinventory.local',
    'ns.local',
    'neuro.local',
    'stock.local',
    'ai.local',
]
'''
    
    print("⚙️ Django Settings Update:")
    print("=" * 40)
    print("Add these domains to ALLOWED_HOSTS in settings.py:")
    print(settings_update)
    
    # Save settings update
    with open("django_settings_update.txt", "w") as f:
        f.write(settings_update)
    
    print("✅ Settings update saved to: django_settings_update.txt")

def show_professional_urls():
    """Show all professional URLs"""
    print("🌐 Your Professional Local URLs:")
    print("=" * 40)
    
    urls = [
        ("neurostock.local:8000", "Main professional domain"),
        ("neurostock-ai.local:8000", "AI-focused branding"),
        ("inventory.neurostock:8000", "Inventory subdomain"),
        ("smart-inventory.local:8000", "Smart inventory focus"),
        ("neuroinventory.local:8000", "Neuro inventory brand"),
        ("ns.local:8000", "Ultra-short domain"),
        ("neuro.local:8000", "Brand-focused short"),
        ("stock.local:8000", "Purpose-clear short"),
        ("ai.local:8000", "AI-focused short")
    ]
    
    for url, desc in urls:
        print(f"   ✅ http://{url} - {desc}")
    
    print(f"\n📱 Mobile Sharing Example:")
    print(f"🧠 NeuroStock AI System")
    print(f"http://neurostock.local:8000")
    print(f"")
    print(f"✨ Professional Local Access")
    print(f"📱 Mobile Optimized Interface")
    print(f"🏠 Secure Local Network")

def show_router_setup():
    """Show router-level setup"""
    print("🌐 Router-Level Professional Setup (Advanced):")
    print("=" * 50)
    print("1. Access your router admin panel:")
    print("   - Usually: http://192.168.1.1 or http://192.168.0.1")
    print("   - Login with admin credentials")
    print()
    print("2. Find DNS/DHCP settings")
    print()
    print("3. Add these local DNS entries:")
    print("   Host: neurostock     → IP: 10.55.157.192")
    print("   Host: neurostock-ai  → IP: 10.55.157.192")
    print("   Host: inventory      → IP: 10.55.157.192")
    print()
    print("4. Save and restart router")
    print()
    print("✅ Result: All devices on network can access:")
    print("   - http://neurostock:8000")
    print("   - http://neurostock-ai:8000")
    print("   - http://inventory:8000")
    print()
    print("🎯 Advantage: No individual device setup needed!")

def main():
    print_header()
    
    system = get_system_info()
    
    print("\n🎯 Local Professional Domain Options:")
    print("   1. 🖥️ Setup Hosts File (Recommended)")
    print("   2. 🌐 Router-Level Setup (Advanced)")
    print("   3. ⚙️ Django Settings Update")
    print("   4. 📱 Show Professional URLs")
    print("   5. 📋 Complete Setup Guide")
    print("   6. ❌ Exit")
    
    choice = input("\n👉 Select option (1-6): ").strip()
    
    if choice == "1":
        if system == "windows":
            setup_windows_hosts()
        else:
            setup_linux_mac_hosts()
    elif choice == "2":
        show_router_setup()
    elif choice == "3":
        update_django_settings()
    elif choice == "4":
        show_professional_urls()
    elif choice == "5":
        # Complete setup
        if system == "windows":
            setup_windows_hosts()
        else:
            setup_linux_mac_hosts()
        print("\n" + "="*50)
        update_django_settings()
        print("\n" + "="*50)
        show_professional_urls()
    elif choice == "6":
        print("👋 Thank you for using NeuroStock AI!")
        sys.exit(0)
    else:
        print("❌ Invalid option. Please try again.")
        main()
    
    print(f"\n🚀 Next Steps:")
    print(f"1. Complete the setup above")
    print(f"2. Run: python manage.py runserver 0.0.0.0:8000")
    print(f"3. Access: http://neurostock.local:8000")
    print(f"4. Share professional domain with team!")

if __name__ == "__main__":
    main()