"""
Management command to set up QR tokens for all users
Run with: python manage.py setup_qr_tokens
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import QRToken, UserProfile


class Command(BaseCommand):
    help = 'Set up QR tokens for all users with profiles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('QR TOKEN SETUP'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        # Get all users with profiles
        users = User.objects.filter(userprofile__isnull=False)
        
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users with profiles found!'))
            return

        created_count = 0
        existing_count = 0

        for user in users:
            try:
                profile = user.userprofile
                token, created = QRToken.objects.get_or_create(user_profile=profile)
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created QR token for {user.username}'
                        )
                    )
                else:
                    existing_count += 1
                    self.stdout.write(
                        f'  Token already exists for {user.username}'
                    )
                
                # Display token info
                self.stdout.write(f'    Token: {token.secure_token}')
                self.stdout.write(f'    Active: {token.is_active}')
                self.stdout.write(f'    URL: /ledger/{token.secure_token}/')
                
                # Display store info if available
                if profile.store_name:
                    self.stdout.write(f'    Store: {profile.store_name}')
                
                self.stdout.write('')  # Empty line
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error for {user.username}: {str(e)}')
                )

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'Total users processed: {users.count()}')
        self.stdout.write(self.style.SUCCESS(f'New tokens created: {created_count}'))
        self.stdout.write(f'Existing tokens: {existing_count}')
        
        if created_count > 0 or existing_count > 0:
            self.stdout.write(self.style.SUCCESS('\n✓ QR token setup complete!'))
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Visit http://localhost:8000/generate-qr/ to see your QR code')
            self.stdout.write('2. Create a bill and print it to see QR code on bill')
            self.stdout.write('3. Scan QR code to test offline ledger access')
        
        self.stdout.write('')
