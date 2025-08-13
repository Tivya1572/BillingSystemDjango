from django.core.management.base import BaseCommand
from BillingApp.models import Product, Denomination

class Command(BaseCommand):
    help = 'Create sample data for the billing system'

    def handle(self, *args, **options):
        # Create sample products
        products_data = [
            {'product_id': 'PROD001', 'name': 'Laptop', 'available_stocks': 50, 'price_per_unit': 50000.0, 'tax_percentage': 18.0},
            {'product_id': 'PROD002', 'name': 'Mouse', 'available_stocks': 200, 'price_per_unit': 500.0, 'tax_percentage': 18.0},
            {'product_id': 'PROD003', 'name': 'Keyboard', 'available_stocks': 150, 'price_per_unit': 1500.0, 'tax_percentage': 18.0},
            {'product_id': 'PROD004', 'name': 'Monitor', 'available_stocks': 75, 'price_per_unit': 15000.0, 'tax_percentage': 18.0},
            {'product_id': 'PROD005', 'name': 'USB Cable', 'available_stocks': 500, 'price_per_unit': 200.0, 'tax_percentage': 12.0},
        ]
        
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                product_id=product_data['product_id'],
                defaults=product_data
            )
            if created:
                self.stdout.write(f'✅ Created product: {product.name}')
            else:
                self.stdout.write(f'⚠️  Product already exists: {product.name}')
        
        # Create denominations
        denominations = [500, 50, 20, 10, 5, 2, 1]
        for value in denominations:
            denom, created = Denomination.objects.get_or_create(
                value=value,
                defaults={'count': 50}  # Start with 50 of each
            )
            if created:
                self.stdout.write(f'✅ Created denomination: ₹{value}')
            else:
                self.stdout.write(f'⚠️  Denomination already exists: ₹{value}')
        
        self.stdout.write(self.style.SUCCESS('🎉 Sample data creation completed!'))