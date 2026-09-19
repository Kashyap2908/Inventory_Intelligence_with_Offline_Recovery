import csv
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from inventory.models import Product, ExpiryStock
from datetime import datetime


class Command(BaseCommand):
    help = "Import Products and ExpiryStock from CSV files"

    def add_arguments(self, parser):
        parser.add_argument(
            '--products',
            type=str,
            default='products.csv',
            help='"D:\Sem-3\Innovation\Stock_Project\smart_inventory\products.csv"'
        )
        parser.add_argument(
            '--stocks',
            type=str,
            default='expiry_stocks.csv',
            help='"D:\Sem-3\Innovation\Stock_Project\smart_inventory\expiry_stocks.csv"'
        )

    def handle(self, *args, **kwargs):
        products_file = kwargs['products']
        stocks_file = kwargs['stocks']
        
        products_imported = 0
        stocks_imported = 0
        
        # IMPORT PRODUCTS FIRST
        self.stdout.write(self.style.WARNING(f'📦 Importing products from {products_file}...'))
        try:
            with open(products_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        defaults = {
                            'name': row['name'],
                            'category': row['category'],
                            'cost_price': row['cost_price'],
                            'selling_price': row['selling_price'],
                            'new_price': row['new_price'],
                            'trend_score': row.get('trend_score', 5.0),
                        }
                        
                        # Add optional fields if they exist
                        if 'abc_classification' in row:
                            defaults['abc_classification'] = row['abc_classification']
                        if 'discount_percentage' in row:
                            defaults['discount_percentage'] = row['discount_percentage']
                        
                        product, created = Product.objects.update_or_create(
                            id=row['id'],
                            defaults=defaults
                        )
                        
                        products_imported += 1
                        status = "✅ Created" if created else "🔄 Updated"
                        self.stdout.write(f"  {status}: {product.name}")
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error importing product {row.get('name', 'Unknown')}: {str(e)}")
                        )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Products imported: {products_imported}')
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'❌ File not found: {products_file}')
            )
            return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error reading products file: {str(e)}')
            )
            return

        # IMPORT EXPIRY STOCK
        self.stdout.write(self.style.WARNING(f'\n📦 Importing expiry stocks from {stocks_file}...'))
        try:
            with open(stocks_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        product = Product.objects.get(id=row['product_id'])
                        
                        # Get user if user_id is provided
                        user = None
                        if 'user_id' in row and row['user_id']:
                            try:
                                user = User.objects.get(id=row['user_id'])
                            except User.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f"  ⚠️ User ID {row['user_id']} not found, skipping user assignment")
                                )
                        
                        defaults = {
                            'product': product,
                            'quantity': row['quantity'],
                            'expiry_date': row['expiry_date'],
                        }
                        
                        if user:
                            defaults['user'] = user
                        
                        stock, created = ExpiryStock.objects.update_or_create(
                            id=row['id'],
                            defaults=defaults
                        )
                        
                        stocks_imported += 1
                        status = "✅ Created" if created else "🔄 Updated"
                        user_info = f" (User: {user.username})" if user else ""
                        self.stdout.write(
                            f"  {status}: {product.name} - {stock.quantity} units{user_info}"
                        )
                        
                    except Product.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Product ID {row['product_id']} not found")
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ Error importing stock: {str(e)}")
                        )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Expiry stocks imported: {stocks_imported}')
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.WARNING(f'⚠️ File not found: {stocks_file} (skipping stocks import)')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error reading stocks file: {str(e)}')
            )

        # SUMMARY
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('🎉 Import completed successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"📊 Products imported/updated: {products_imported}")
        self.stdout.write(f"📦 Stocks imported/updated: {stocks_imported}")
