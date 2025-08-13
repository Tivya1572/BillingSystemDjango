from django.db import models
from django.core.validators import MinValueValidator
import uuid

class Product(models.Model):
    product_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    available_stocks = models.PositiveIntegerField(default=0)
    price_per_unit = models.FloatField(validators=[MinValueValidator(0.0)])
    tax_percentage = models.FloatField(validators=[MinValueValidator(0.0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.product_id})"

    class Meta:
        ordering = ['name']

class Customer(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class Purchase(models.Model):
    purchase_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    total_amount = models.FloatField(default=0.0)
    tax_amount = models.FloatField(default=0.0)
    net_amount = models.FloatField(default=0.0)
    rounded_amount = models.FloatField(default=0.0)
    cash_paid = models.FloatField(default=0.0)
    balance_amount = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Purchase {self.purchase_id} - {self.customer.email}"

    class Meta:
        ordering = ['-created_at']

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.FloatField()
    tax_percentage = models.FloatField()
    tax_amount = models.FloatField()
    total_price = models.FloatField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

class Denomination(models.Model):
    value = models.IntegerField(unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"₹{self.value} x {self.count}"

    class Meta:
        ordering = ['-value']

class BalanceDenomination(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='balance_denominations')
    denomination_value = models.IntegerField()
    count = models.PositiveIntegerField()

    def __str__(self):
        return f"₹{self.denomination_value} x {self.count}"