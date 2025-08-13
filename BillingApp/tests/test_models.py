from django.test import TestCase
from BillingApp.models import Product, Customer, Purchase

class ProductModelTest(TestCase):
    def test_product_creation(self):
        product = Product.objects.create(
            product_id="TEST001",
            name="Test Product",
            available_stocks=100,
            price_per_unit=25.50,
            tax_percentage=18.0
        )
        self.assertEqual(product.product_id, "TEST001")
        self.assertEqual(str(product), "Test Product (TEST001)")