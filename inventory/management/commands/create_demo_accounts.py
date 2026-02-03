from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import UserProfile

class Command(BaseCommand):
    help = 'Create demo accounts for NeuroStock system'

    def handle(self, *args, **options):
        demo_accounts = [
            {
                'username': 'admin',
                'email': 'admin@neurostock.com',
                'password': 'admin123',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin'
            },
            {
                'username': 'inventory',
                'email': 'inventory@neurostock.com',
                'password': 'admin123',
                'first_name': 'Inventory',
                'last_name': 'Manager',
                'role': 'inventory'
            },
            {
                'username': 'marketing',
                'email': 'marketing@neurostock.com',
                'password': 'admin123',
                'first_name': 'Marketing',
                'last_name': 'Analyst',
                'role': 'marketing'
            }
        ]

        for account_data in demo_accounts:
            try:
                # Check if user already exists
                if User.objects.filter(email=account_data['email']).exists():
                    self.stdout.write(
                        self.style.WARNING(f"User with email {account_data['email']} already exists")
                    )
                    continue

                # Create user
                user = User.objects.create_user(
                    username=account_data['username'],
                    email=account_data['email'],
                    password=account_data['password'],
                    first_name=account_data['first_name'],
                    last_name=account_data['last_name']
                )

                # Create or update user profile
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': account_data['role']}
                )

                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Created demo account: {account_data['email']} ({account_data['role']})")
                    )
                else:
                    profile.role = account_data['role']
                    profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Updated demo account: {account_data['email']} ({account_data['role']})")
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error creating account {account_data['email']}: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS('\n🎯 Demo accounts setup complete!')
        )
        self.stdout.write('📧 You can now login with:')
        self.stdout.write('   • admin@neurostock.com / admin123 (Admin)')
        self.stdout.write('   • inventory@neurostock.com / admin123 (Inventory Manager)')
        self.stdout.write('   • marketing@neurostock.com / admin123 (Marketing Analyst)')
        self.stdout.write('   • Or create new accounts by entering any email!')