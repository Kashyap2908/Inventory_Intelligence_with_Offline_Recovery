"""
Automatic Trend Score Calculator
Calculates trend scores based on:
- Stock levels
- Sales frequency
- Product requests
- Time-based patterns
"""

from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


def calculate_trend_score(product):
    """
    Calculate trend score for a product (0-10 scale)
    Higher score = Higher demand/better performance
    """
    score = 5.0  # Base score
    
    # Factor 1: Stock Movement (30% weight)
    stock_score = calculate_stock_movement_score(product)
    score += stock_score * 0.3
    
    # Factor 2: Sales Frequency (30% weight)
    sales_score = calculate_sales_frequency_score(product)
    score += sales_score * 0.3
    
    # Factor 3: Request Frequency (20% weight)
    request_score = calculate_request_frequency_score(product)
    score += request_score * 0.2
    
    # Factor 4: Stock Level (20% weight)
    stock_level_score = calculate_stock_level_score(product)
    score += stock_level_score * 0.2
    
    # Ensure score is between 0 and 10
    score = max(0.0, min(10.0, score))
    
    return round(score, 1)


def calculate_stock_movement_score(product):
    """
    Score based on how frequently stock is added/removed
    More movement = Higher demand
    """
    from inventory.models import ExpiryStock
    
    # Count stock entries in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_stock_entries = ExpiryStock.objects.filter(
        product=product,
        created_at__gte=thirty_days_ago
    ).count()
    
    # Score: 0-5 based on entries
    if recent_stock_entries >= 10:
        return 5.0
    elif recent_stock_entries >= 7:
        return 4.0
    elif recent_stock_entries >= 5:
        return 3.0
    elif recent_stock_entries >= 3:
        return 2.0
    elif recent_stock_entries >= 1:
        return 1.0
    else:
        return 0.0


def calculate_sales_frequency_score(product):
    """
    Score based on billing frequency
    More bills = Higher demand
    """
    from inventory.models import SalesBillItem
    
    # Count bills in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_bills = SalesBillItem.objects.filter(
        product=product,
        bill__created_at__gte=thirty_days_ago
    ).count()
    
    # Score: 0-5 based on bills
    if recent_bills >= 15:
        return 5.0
    elif recent_bills >= 10:
        return 4.0
    elif recent_bills >= 7:
        return 3.0
    elif recent_bills >= 4:
        return 2.0
    elif recent_bills >= 1:
        return 1.0
    else:
        return 0.0


def calculate_request_frequency_score(product):
    """
    Score based on product requests from inventory users
    More requests = Higher demand
    """
    from inventory.models import OrderQueue
    
    # Count requests in last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_requests = OrderQueue.objects.filter(
        product=product,
        created_at__gte=thirty_days_ago,
        requested_by__isnull=False  # Only inventory requests
    ).count()
    
    # Score: 0-5 based on requests
    if recent_requests >= 10:
        return 5.0
    elif recent_requests >= 7:
        return 4.0
    elif recent_requests >= 5:
        return 3.0
    elif recent_requests >= 3:
        return 2.0
    elif recent_requests >= 1:
        return 1.0
    else:
        return 0.0


def calculate_stock_level_score(product):
    """
    Score based on current stock level
    Low stock with activity = High demand
    """
    total_stock = product.total_stock
    
    # Get recent activity (bills + requests in last 7 days)
    from inventory.models import SalesBillItem, OrderQueue
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    recent_activity = (
        SalesBillItem.objects.filter(
            product=product,
            bill__created_at__gte=seven_days_ago
        ).count() +
        OrderQueue.objects.filter(
            product=product,
            created_at__gte=seven_days_ago
        ).count()
    )
    
    # If low stock but high activity = High demand
    if total_stock < 20 and recent_activity >= 3:
        return 5.0
    elif total_stock < 50 and recent_activity >= 2:
        return 3.0
    elif total_stock < 100 and recent_activity >= 1:
        return 2.0
    elif total_stock >= 200 and recent_activity == 0:
        return -2.0  # Overstocked, low demand
    else:
        return 0.0


def update_all_trend_scores():
    """
    Update trend scores for all products
    Call this periodically (e.g., daily via cron job)
    """
    from inventory.models import Product
    
    updated_count = 0
    for product in Product.objects.all():
        old_score = product.trend_score
        new_score = calculate_trend_score(product)
        
        if old_score != new_score:
            product.trend_score = new_score
            product.last_trend_update = timezone.now()
            product.save()
            updated_count += 1
    
    return updated_count


def update_product_trend_score(product):
    """
    Update trend score for a single product
    Call this when product activity happens
    """
    new_score = calculate_trend_score(product)
    product.trend_score = new_score
    product.last_trend_update = timezone.now()
    product.save()
    return new_score
