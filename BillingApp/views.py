from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from .models import Product, Customer, Purchase, PurchaseItem, Denomination, BalanceDenomination
from .utils import calculate_balance_denominations, update_denomination_stock, send_invoice_email, calculate_bill_totals
import json
import logging

logger = logging.getLogger(__name__)

def billing_form(request):
    """Main billing form view"""
    if request.method == 'POST':
        return process_billing_form(request)
    
    # Get initial denominations
    denominations = Denomination.objects.all().order_by('-value')
    if not denominations.exists():
        # Create default denominations
        default_denominations = [500, 50, 20, 10, 5, 2, 1]
        for value in default_denominations:
            Denomination.objects.create(value=value, count=10)
        denominations = Denomination.objects.all().order_by('-value')
    
    context = {
        'denominations': denominations,
        'products': Product.objects.all()
    }
    return render(request, 'billing/billing_form.html', context)

def process_billing_form(request):
    """Process the billing form submission"""
    try:
        # Handle both JSON and regular form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        # Extract form data
        customer_email = data.get('customer_email')
        # items_data = data.get('items', [])
        # Handle product_id and quantity (support both single + [] format)
        product_ids = request.POST.getlist('product_id') + request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity') + request.POST.getlist('quantity[]')
        denominations_received = data.get('denominations', {})
        cash_paid = float(data.get('cash_paid', 0))

        items_data = []
        for pid, qty in zip(product_ids, quantities):
            if pid and qty:
                items_data.append({
                    'product_id': pid,
                    'quantity': qty
                })
        
        # Validate required fields
        if not customer_email:
            return JsonResponse({'error': 'Customer email is required'}, status=400)
        
        if not items_data:
            return JsonResponse({'error': 'At least one item is required'}, status=400)
        
        if cash_paid <= 0:
            return JsonResponse({'error': 'Cash paid must be greater than 0'}, status=400)
        
        # Validate products and calculate totals
        validated_items = []
        for item in items_data:
            try:
                product = Product.objects.get(product_id=item['product_id'])
                quantity = int(item['quantity'])
                
                if quantity <= 0:
                    return JsonResponse({
                        'error': f'Quantity must be greater than 0 for {product.name}'
                    }, status=400)
                
                if quantity > product.available_stocks:
                    return JsonResponse({
                        'error': f'Insufficient stock for {product.name}. Available: {product.available_stocks}'
                    }, status=400)
                
                validated_items.append({
                    'product': product,
                    'quantity': quantity,
                    'unit_price': product.price_per_unit,
                    'tax_percentage': product.tax_percentage
                })
            except Product.DoesNotExist:
                return JsonResponse({'error': f'Product {item["product_id"]} not found'}, status=400)
            except (ValueError, KeyError) as e:
                return JsonResponse({'error': f'Invalid item data: {str(e)}'}, status=400)
        
        # Calculate bill totals
        totals = calculate_bill_totals(validated_items)
        balance_amount = cash_paid - totals['rounded_amount']
        
        if balance_amount < 0:
            return JsonResponse({'error': 'Insufficient payment'}, status=400)
        
        # Calculate balance denominations only if there's a balance
        balance_denominations = {}
        remaining = 0
        if balance_amount > 0:
            balance_denominations, remaining = calculate_balance_denominations(balance_amount)
            
            if remaining > 0:
                return JsonResponse({
                    'error': f'Cannot provide exact change. Short by ₹{remaining}'
                }, status=400)
        
        # Process the transaction
        with transaction.atomic():
            # Check if customer already exists by email (case-insensitive match)
            customer = Customer.objects.filter(email__iexact=customer_email).first()
            
            if not customer:
                # Create new customer
                customer = Customer.objects.create(
                    email=customer_email
                )
            
            # Create purchase
            purchase = Purchase.objects.create(
                customer=customer,
                total_amount=totals['total_without_tax'],
                tax_amount=totals['total_tax'],
                net_amount=totals['net_amount'],
                rounded_amount=totals['rounded_amount'],
                cash_paid=cash_paid,
                balance_amount=balance_amount
            )
            
            # Create purchase items and update stock
            for item in validated_items:
                product = item['product']
                quantity = item['quantity']
                
                item_total = item['unit_price'] * quantity
                item_tax = (item_total * item['tax_percentage']) / 100
                
                PurchaseItem.objects.create(
                    purchase=purchase,
                    product=product,
                    quantity=quantity,
                    unit_price=item['unit_price'],
                    tax_percentage=item['tax_percentage'],
                    tax_amount=item_tax,
                    total_price=item_total + item_tax
                )
                
                # Update product stock
                product.available_stocks -= quantity
                product.save()
            
            # Save balance denominations only if there are any
            if balance_denominations:
                for value, count in balance_denominations.items():
                    if count > 0:
                        BalanceDenomination.objects.create(
                            purchase=purchase,
                            denomination_value=value,
                            count=count
                        )
                
                # Update denomination stock
                received_denominations = {
                    int(k): int(v) for k, v in denominations_received.items() 
                    if int(v) > 0
                }
                update_denomination_stock(balance_denominations, received_denominations)
            
            # Send invoice email (asynchronously in production)
            try:
                send_invoice_email(purchase)
            except Exception as e:
                logger.warning(f"Failed to send email for purchase {purchase.purchase_id}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'purchase_id': str(purchase.purchase_id),
            'redirect_url': f'/bill/{purchase.purchase_id}/'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error processing billing form: {str(e)}")
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)

def bill_detail(request, purchase_id):
    """Display bill detail page"""
    purchase = get_object_or_404(Purchase, purchase_id=purchase_id)
    context = {
        'purchase': purchase,
        'items': purchase.items.all(),
        'balance_denominations': purchase.balance_denominations.all()
    }
    return render(request, 'billing/bill_detail.html', context)

def purchase_history(request):
    """Display purchase history"""
    email = request.GET.get('email', '')
    purchases = Purchase.objects.all().order_by('-created_at')
    
    if email:
        purchases = purchases.filter(customer__email__icontains=email)
    
    paginator = Paginator(purchases, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'email_filter': email
    }
    return render(request, 'billing/purchase_history.html', context)


def get_product_info(request):
    """AJAX endpoint to get product information"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            
            if not product_id:
                return JsonResponse({'success': False, 'error': 'Product ID is required'})
            
            product = Product.objects.get(product_id=product_id)
            return JsonResponse({
                'success': True,
                'product': {
                    'name': product.name,
                    'price': float(product.price_per_unit),
                    'tax_percentage': float(product.tax_percentage),
                    'available_stocks': product.available_stocks
                }
            })
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
        except Exception as e:
            logger.error(f"Error in get_product_info: {str(e)}")
            return JsonResponse({'success': False, 'error': 'Internal server error'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})