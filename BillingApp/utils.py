from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Denomination, BalanceDenomination
import math

def calculate_balance_denominations(balance_amount):
    """Calculate the minimum denominations needed for balance"""
    denominations = [500, 50, 20, 10, 5, 2, 1]
    available_denominations = {}
    
    # Get available denominations from database
    for denom in Denomination.objects.all():
        available_denominations[denom.value] = denom.count
    
    balance_denominations = {}
    remaining_balance = int(balance_amount)
    
    for denom in denominations:
        if denom in available_denominations and remaining_balance >= denom:
            available_count = available_denominations[denom]
            needed_count = min(remaining_balance // denom, available_count)
            
            if needed_count > 0:
                balance_denominations[denom] = needed_count
                remaining_balance -= denom * needed_count
    
    return balance_denominations, remaining_balance

def update_denomination_stock(denominations_used, denominations_received):
    """Update denomination stock after a transaction"""
    # Subtract used denominations
    for value, count in denominations_used.items():
        denom, created = Denomination.objects.get_or_create(value=value, defaults={'count': 0})
        denom.count = max(0, denom.count - count)
        denom.save()
    
    # Add received denominations
    for value, count in denominations_received.items():
        if count > 0:
            denom, created = Denomination.objects.get_or_create(value=value, defaults={'count': 0})
            denom.count += count
            denom.save()

def send_invoice_email(purchase):
    """Send invoice email to customer"""
    subject = f'Invoice - Purchase #{purchase.purchase_id}'
    message = f'Thank you for your purchase! Purchase ID: {purchase.purchase_id}'
    
    try:
        send_mail(
            subject,
            message,
            'noreply@example.com',
            [purchase.customer.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def calculate_bill_totals(items_data):
    """Calculate bill totals from items data"""
    total_without_tax = 0
    total_tax = 0
    
    for item in items_data:
        item_total = item['unit_price'] * item['quantity']
        item_tax = (item_total * item['tax_percentage']) / 100
        total_without_tax += item_total
        total_tax += item_tax
    
    net_amount = total_without_tax + total_tax
    rounded_amount = math.ceil(net_amount)  # Round up to nearest rupee
    
    return {
        'total_without_tax': round(total_without_tax, 2),
        'total_tax': round(total_tax, 2),
        'net_amount': round(net_amount, 2),
        'rounded_amount': rounded_amount
    }