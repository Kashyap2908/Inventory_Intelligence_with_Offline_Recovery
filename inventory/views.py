from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F
from django.utils import timezone
from datetime import date, timedelta
import json

from .models import Product, ExpiryStock, OrderQueue, SalesBill, SalesBillItem, UserProfile, Notification
# AIRecommendation model will be added after migration
try:
    from .models import AIRecommendation
except ImportError:
    AIRecommendation = None
from .forms import ProductForm, StockEntryForm, OrderForm, DiscountForm, SalesForm, SignUpForm

def test_ai_connection():
    """Test function to verify Google Gemini AI connection"""
    try:
        import google.generativeai as genai
        from config import GOOGLE_API_KEY
        
        if GOOGLE_API_KEY == "AIzaSyA-iOTJn6vAs1JHz22fobYTr9iPoqLh2-I" or not GOOGLE_API_KEY:
            return False, "API key not configured"
        
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Test with a simple prompt
        test_prompt = "Respond with just the number 5.0 if you can understand this message."
        response = model.generate_content(test_prompt)
        
        if "5.0" in response.text:
            return True, "AI connection successful"
        else:
            return False, f"Unexpected response: {response.text}"
            
    except Exception as e:
        return False, f"Connection failed: {str(e)}"

def auto_remove_expired_products():
    """Automatically remove expired products and create notifications"""
    from datetime import date
    
    today = date.today()
    expired_batches = ExpiryStock.objects.filter(
        expiry_date__lt=today,
        quantity__gt=0
    )
    
    if not expired_batches.exists():
        return 0, 0  # No expired products
    
    removed_count = 0
    total_quantity_removed = 0
    products_affected = set()
    
    for batch in expired_batches:
        product = batch.product
        expired_quantity = batch.quantity
        days_expired = (today - batch.expiry_date).days
        
        products_affected.add(product)
        
        # Create notification about expired product removal
        Notification.objects.create(
            title=f"EXPIRED REMOVED: {product.name}",
            message=f"Removed {expired_quantity} units of {product.name} "
                   f"(expired {days_expired} days ago). "
                   f"Automatic safety removal completed.",
            notification_type='expiry_warning',
            priority='high',
            target_user_role='all',
            product=product
        )
        
        # Remove the expired batch
        batch.delete()
        removed_count += 1
        total_quantity_removed += expired_quantity
    
    # Check products with zero stock after expiry removal
    for product in products_affected:
        if product.total_stock == 0:
            Notification.objects.create(
                title=f"URGENT REORDER: {product.name}",
                message=f"{product.name} is now out of stock due to expiry removal. "
                       f"Immediate reorder required for continued sales.",
                notification_type='low_stock',
                priority='urgent',
                target_user_role='all',
                product=product
            )
    
    return removed_count, total_quantity_removed

def generate_notifications():
    """Generate automatic notifications for inventory management"""
    from datetime import date, timedelta
    
    # First, automatically remove expired products
    removed_count, removed_quantity = auto_remove_expired_products()
    
    if removed_count > 0:
        print(f"🗑️ Auto-removed {removed_count} expired batches ({removed_quantity} units)")
    
    # Clear old notifications (older than 7 days)
    old_notifications = Notification.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=7)
    )
    old_notifications.delete()
    
    # Get all products with stock
    products = Product.objects.all()
    
    for product in products:
        # Check for expiry warnings (products expiring in next 15 days)
        near_expiry_stock = product.expirystock_set.filter(
            quantity__gt=0,
            expiry_date__lte=date.today() + timedelta(days=15),
            expiry_date__gte=date.today()
        ).order_by('expiry_date')
        
        if near_expiry_stock.exists():
            earliest_batch = near_expiry_stock.first()
            days_left = (earliest_batch.expiry_date - date.today()).days
            
            # Check if notification already exists for this product today
            existing_notification = Notification.objects.filter(
                product=product,
                notification_type='expiry_warning',
                created_at__date=date.today()
            ).exists()
            
            if not existing_notification:
                if days_left <= 3:
                    priority = 'urgent'
                    title = f"🚨 URGENT: {product.name} expires in {days_left} days!"
                elif days_left <= 7:
                    priority = 'high'
                    title = f"⚠️ HIGH: {product.name} expires in {days_left} days"
                else:
                    priority = 'medium'
                    title = f"📅 {product.name} expires in {days_left} days"
                
                message = f"Product: {product.name}\nQuantity: {earliest_batch.quantity} units\nExpiry Date: {earliest_batch.expiry_date.strftime('%B %d, %Y')}\nAction: Move to front for FEFO (First Expired, First Out)"
                
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type='expiry_warning',
                    priority=priority,
                    target_user_role='inventory',
                    product=product
                )
        
        # Check for low stock warnings
        total_stock = product.total_stock
        if total_stock < 20:  # Low stock threshold
            existing_low_stock = Notification.objects.filter(
                product=product,
                notification_type='low_stock',
                created_at__date=date.today()
            ).exists()
            
            if not existing_low_stock:
                if total_stock == 0:
                    priority = 'urgent'
                    title = f"🚨 OUT OF STOCK: {product.name}"
                elif total_stock < 5:
                    priority = 'high'
                    title = f"⚠️ CRITICAL LOW: {product.name} ({total_stock} units)"
                else:
                    priority = 'medium'
                    title = f"📦 Low Stock: {product.name} ({total_stock} units)"
                
                message = f"Product: {product.name}\nCurrent Stock: {total_stock} units\nRecommendation: Reorder immediately to avoid stockout"
                
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type='low_stock',
                    priority=priority,
                    target_user_role='inventory',
                    product=product
                )

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'login.html')
        
        # Authenticate using username and password
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            try:
                profile = user.userprofile
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                if profile.role == 'inventory':
                    return redirect('inventory_dashboard')
                elif profile.role == 'marketing':
                    return redirect('trend_dashboard')
                elif profile.role == 'admin':
                    return redirect('admin_dashboard')
            except UserProfile.DoesNotExist:
                return redirect('inventory_dashboard')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        role = request.POST.get('role', '').strip()
        
        # Validation
        if not all([username, email, password, confirm_password, role]):
            messages.error(request, 'All fields are required.')
            return render(request, 'signup.html')
        
        if len(username) < 3:
            messages.error(request, 'Username must be at least 3 characters long.')
            return render(request, 'signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long.')
            return render(request, 'signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html')
        
        if role not in ['inventory', 'marketing', 'admin']:
            messages.error(request, 'Please select a valid role.')
            return render(request, 'signup.html')
        
        # Check if username or email already exists
        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists. Please choose a different username.')
            return render(request, 'signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered. Please use a different email.')
            return render(request, 'signup.html')
        
        try:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=username.title()  # Use username as first name
            )
            
            # Create user profile with selected role
            UserProfile.objects.create(
                user=user,
                role=role
            )
            
            # Auto-login the new user
            login(request, user)
            
            # Redirect to appropriate dashboard based on role
            messages.success(request, f'🎉 Welcome to NeuroStock, {username}! Your account has been created successfully.')
            
            if role == 'inventory':
                return redirect('inventory_dashboard')
            elif role == 'marketing':
                return redirect('trend_dashboard')
            elif role == 'admin':
                return redirect('admin_dashboard')
            else:
                return redirect('inventory_dashboard')  # Default fallback
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'signup.html')

@login_required
def inventory_dashboard(request):
    # Generate notifications first
    generate_notifications()
    
    products = Product.objects.all()
    recent_stock = ExpiryStock.objects.order_by('-created_at')[:10]
    
    # Get unread notifications for inventory role
    notifications_queryset = Notification.objects.filter(
        target_user_role__in=['inventory', 'all'],
        is_read=False
    ).order_by('-priority', '-created_at')
    
    # Get read notifications for history (last 20)
    try:
        read_notifications = Notification.objects.filter(
            target_user_role__in=['inventory', 'all'],
            is_read=True
        ).order_by('-created_at')[:20]  # Use created_at instead of updated_at
    except Exception:
        # Fallback if there are any database issues
        read_notifications = Notification.objects.filter(
            target_user_role__in=['inventory', 'all'],
            is_read=True
        ).order_by('-created_at')[:20]
    
    # Count notifications by priority (before slicing)
    urgent_count = notifications_queryset.filter(priority='urgent').count()
    high_count = notifications_queryset.filter(priority='high').count()
    total_notifications = notifications_queryset.count()
    
    # Now slice for display (limit to 10)
    notifications = notifications_queryset[:10]
    
    if request.method == 'POST':
        if 'add_product' in request.POST:
            form = ProductForm(request.POST)
            if form.is_valid():
                product = form.save()
                product.new_price = product.selling_price
                product.save()
                messages.success(request, 'Product added successfully!')
                return redirect('inventory_dashboard')
        
        elif 'add_stock' in request.POST:
            stock_form = StockEntryForm(request.POST)
            if stock_form.is_valid():
                stock_form.save()
                messages.success(request, 'Stock added successfully!')
                return redirect('inventory_dashboard')
        
        elif 'mark_read' in request.POST or request.POST.get('notification_id'):
            print(f"DEBUG: Mark read request received")
            print(f"DEBUG: POST data: {request.POST}")
            print(f"DEBUG: Is AJAX: {request.headers.get('X-Requested-With') == 'XMLHttpRequest'}")
            
            notification_id = request.POST.get('notification_id')
            print(f"DEBUG: Notification ID: {notification_id}")
            
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id)
                    print(f"DEBUG: Found notification: {notification.title}")
                    print(f"DEBUG: Before update - is_read: {notification.is_read}")
                    
                    notification.is_read = True
                    # Manually set the updated_at to current time
                    from django.utils import timezone
                    notification.updated_at = timezone.now()
                    notification.save(update_fields=['is_read', 'updated_at'])
                    
                    # Refresh from database to confirm
                    notification.refresh_from_db()
                    print(f"DEBUG: After update - is_read: {notification.is_read}")
                    print(f"DEBUG: Using created_at as timestamp: {notification.created_at}")
                    
                    # Check if it's an AJAX request
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        print(f"DEBUG: Returning JSON response")
                        return JsonResponse({
                            'success': True,
                            'message': 'Notification marked as read!'
                        })
                    else:
                        messages.success(request, 'Notification marked as read!')
                        return redirect('inventory_dashboard')
                        
                except Notification.DoesNotExist:
                    print(f"DEBUG: Notification not found with ID: {notification_id}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Notification not found'
                        })
                    else:
                        messages.error(request, 'Notification not found!')
                        return redirect('inventory_dashboard')
                except Exception as e:
                    print(f"DEBUG: Error marking as read: {e}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': str(e)
                        })
            
            print(f"DEBUG: No notification ID provided")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'No notification ID provided'
                })
            else:
                return redirect('inventory_dashboard')
        
        elif 'mark_all_read' in request.POST:
            notification_ids_json = request.POST.get('notification_ids')
            if notification_ids_json:
                try:
                    import json
                    notification_ids = json.loads(notification_ids_json)
                    
                    # Mark all specified notifications as read
                    updated_count = Notification.objects.filter(
                        id__in=notification_ids,
                        target_user_role__in=['inventory', 'all'],
                        is_read=False
                    ).update(is_read=True)
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': f'{updated_count} notifications marked as read!'
                        })
                    else:
                        messages.success(request, f'{updated_count} notifications marked as read!')
                        return redirect('inventory_dashboard')
                        
                except (json.JSONDecodeError, ValueError) as e:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Invalid notification IDs'
                        })
                    else:
                        messages.error(request, 'Invalid notification data!')
                        return redirect('inventory_dashboard')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'No notification IDs provided'
                })
            else:
                return redirect('inventory_dashboard')
    
    product_form = ProductForm()
    stock_form = StockEntryForm()
    
    context = {
        'products': products,
        'recent_stock': recent_stock,
        'product_form': product_form,
        'stock_form': stock_form,
        'notifications': notifications,
        'read_notifications': read_notifications,
        'urgent_count': urgent_count,
        'high_count': high_count,
        'total_notifications': total_notifications,
    }
    return render(request, 'inventory_dashboard.html', context)

@login_required
def trend_dashboard(request):
    from django.utils import timezone
    
    products = Product.objects.all()
    
    if request.method == 'POST' and 'update_trends' in request.POST:
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Real-time trend analysis when user clicks the button
            import sqlite3
            import time
            import random
            from django.conf import settings
            from datetime import datetime
            
            check_start_time = timezone.now()
            print(f"🕐 Real-Time Trend Analysis Started at: {check_start_time.strftime('%H:%M:%S')}")
            
            try:
                # Try Google Gemini AI first
                import google.generativeai as genai
                
                try:
                    from config import GOOGLE_API_KEY
                except ImportError:
                    GOOGLE_API_KEY = "AIzaSyA-iOTJn6vAs1JHz22fobYTr9iPoqLh2-I"
                
                # If valid API key, use AI analysis
                if GOOGLE_API_KEY and GOOGLE_API_KEY != "AIzaSyA-iOTJn6vAs1JHz22fobYTr9iPoqLh2-I":
                    print("🤖 Using Google Gemini AI for trend analysis")
                    genai.configure(api_key=GOOGLE_API_KEY)
                    model = genai.GenerativeModel('gemini-flash-latest')
                    
                    updated_count = 0
                    for product in products:
                        current_time = timezone.now().strftime('%H:%M:%S')
                        print(f"[{current_time}] AI Analyzing: {product.name}")
                        
                        prompt = f"""Analyze market trend for {product.name} in {product.category} category.
Current stock: {product.total_stock} units
Current time: {current_time}

Provide trend score 0.0-10.0 based on:
- Market demand for {product.category}
- Seasonal trends for {timezone.now().strftime('%B')}
- Stock levels and consumer behavior

Format: SCORE,RECOMMENDATION
Example: "7.5,High demand expected"
"""
                        
                        try:
                            response = model.generate_content(prompt)
                            ai_response = response.text.strip()
                            
                            if ',' in ai_response:
                                score_str = ai_response.split(',')[0].strip()
                                trend_score = float(score_str)
                                trend_score = min(10.0, max(0.0, trend_score))
                                
                                # Update product
                                old_score = product.trend_score
                                product.trend_score = trend_score
                                product.last_trend_update = timezone.now()
                                product.save(update_fields=['trend_score', 'last_trend_update'])
                                
                                print(f"   ✅ {product.name}: {old_score} → {trend_score}")
                                updated_count += 1
                                
                                time.sleep(1)  # Rate limiting
                            
                        except Exception as e:
                            print(f"   ❌ AI Error for {product.name}: {e}")
                            # Fallback to intelligent simulation
                            old_score = product.trend_score
                            new_score = generate_realistic_trend_score(product)
                            product.trend_score = new_score
                            product.last_trend_update = timezone.now()
                            product.save(update_fields=['trend_score', 'last_trend_update'])
                            print(f"   🔄 Fallback {product.name}: {old_score} → {new_score}")
                            updated_count += 1
                
                else:
                    # Use intelligent simulation when no AI available
                    print("🔄 Using Intelligent Market Simulation")
                    updated_count = 0
                    
                    for product in products:
                        current_time = timezone.now().strftime('%H:%M:%S')
                        print(f"[{current_time}] Analyzing: {product.name}")
                        
                        old_score = product.trend_score
                        new_score = generate_realistic_trend_score(product)
                        
                        product.trend_score = new_score
                        product.last_trend_update = timezone.now()
                        product.save(update_fields=['trend_score', 'last_trend_update'])
                        
                        print(f"   ✅ {product.name}: {old_score} → {new_score}")
                        updated_count += 1
                        
                        time.sleep(0.1)  # Small delay for realism
                
                # Calculate updated KPI data
                updated_products = Product.objects.all()
                high_demand = updated_products.filter(trend_score__gte=7).count()
                low_demand = updated_products.filter(trend_score__lt=4).count()
                
                price_actions_count = 0
                for product in updated_products:
                    if (product.trend_score >= 7 and product.total_stock >= 100) or \
                       (product.trend_score < 3 and product.total_stock > 150):
                        price_actions_count += 1
                
                latest_update = updated_products.filter(last_trend_update__isnull=False).order_by('-last_trend_update').first()
                
                # Prepare response data
                products_data = []
                for product in updated_products:
                    products_data.append({
                        'id': product.id,
                        'name': product.name,
                        'category': product.category,
                        'total_stock': product.total_stock,
                        'trend_score': float(product.trend_score),
                        'last_trend_update': product.last_trend_update.isoformat() if product.last_trend_update else None,
                    })
                
                check_end_time = timezone.now()
                duration = (check_end_time - check_start_time).total_seconds()
                
                print(f"✅ Trend Analysis Complete! Updated {updated_count} products in {duration:.1f}s")
                
                return JsonResponse({
                    'success': True,
                    'message': f'🎯 Real-Time Trend Analysis Complete! Updated {updated_count} products at {check_end_time.strftime("%H:%M:%S")} (Duration: {duration:.1f}s)',
                    'products': products_data,
                    'kpi_data': {
                        'high_demand_count': high_demand,
                        'low_demand_count': low_demand,
                        'price_actions_count': price_actions_count,
                    },
                    'last_updated': latest_update.last_trend_update.isoformat() if latest_update else None,
                })
                
            except ImportError:
                print("❌ Google AI library not available, using simulation")
                return enhanced_simulation_ajax_update(request, products)
            except Exception as e:
                print(f"❌ Error in trend analysis: {e}")
                return JsonResponse({
                    'success': False,
                    'error': f'Trend analysis failed: {str(e)}'
                })
            # Will be restored after testing basic AJAX functionality
        else:
            print("📄 Regular form submission detected")
            # Handle regular form submission (fallback)
            return enhanced_simulation_update(request, products)
    
    # Calculate trend statistics for display
    high_demand = products.filter(trend_score__gte=7).count()
    moderate_demand = products.filter(trend_score__gte=4, trend_score__lt=7).count()
    low_demand = products.filter(trend_score__lt=4).count()
    
    # Calculate price actions count (products that need price adjustments)
    price_actions_count = 0
    for product in products:
        if (product.trend_score >= 7 and product.total_stock >= 100) or \
           (product.trend_score < 3 and product.total_stock > 150):
            price_actions_count += 1
    
    # Get the most recent update time
    latest_update = products.filter(last_trend_update__isnull=False).order_by('-last_trend_update').first()
    
    context = {
        'products': products,
        'high_demand_count': high_demand,
        'moderate_demand_count': moderate_demand,
        'low_demand_count': low_demand,
        'price_actions_count': price_actions_count,
        'latest_update': latest_update.last_trend_update if latest_update else None,
    }
    return render(request, 'trend_dashboard.html', context)


@login_required
def get_product_details(request, product_id):
    """Get detailed product information for the eye icon"""
    try:
        product = Product.objects.get(id=product_id)
        
        # Get recent stock entries
        recent_stock = ExpiryStock.objects.filter(product=product).order_by('-created_at')[:5]
        
        # Get recent sales
        recent_sales = SalesBillItem.objects.filter(product=product).order_by('-bill__created_at')[:5]
        
        # Calculate some metrics
        from django.db import models
        total_sales_this_month = SalesBillItem.objects.filter(
            product=product,
            bill__created_at__month=timezone.now().month
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        # Get AI recommendations for this product
        ai_recommendations = AIRecommendation.objects.filter(
            product=product,
            status='pending'
        ).order_by('-created_at')
        
        data = {
            'product': {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'cost_price': float(product.cost_price),
                'selling_price': float(product.selling_price),
                'current_price': float(product.new_price),
                'abc_classification': product.calculated_abc_classification,
                'total_stock': product.total_stock,
                'trend_score': float(product.trend_score),
                'last_trend_update': product.last_trend_update.isoformat() if product.last_trend_update else None,
            },
            'recent_stock': [
                {
                    'quantity': stock.quantity,
                    'expiry_date': stock.expiry_date.strftime('%Y-%m-%d'),
                    'created_at': stock.created_at.strftime('%Y-%m-%d %H:%M'),
                }
                for stock in recent_stock
            ],
            'recent_sales': [
                {
                    'quantity': sale.quantity,
                    'price': float(sale.price),
                    'total': float(sale.total),
                    'date': sale.bill.created_at.strftime('%Y-%m-%d %H:%M'),
                }
                for sale in recent_sales
            ],
            'metrics': {
                'total_sales_this_month': total_sales_this_month,
                'stock_turnover': round(total_sales_this_month / max(product.total_stock, 1), 2),
                'days_of_stock': round(product.total_stock / max(total_sales_this_month / 30, 1), 1) if total_sales_this_month > 0 else 999,
            },
            'ai_recommendations': [
                {
                    'type': rec.recommendation_type,
                    'text': rec.recommendation_text,
                    'suggested_value': float(rec.suggested_value) if rec.suggested_value else None,
                    'suggested_quantity': rec.suggested_quantity,
                }
                for rec in ai_recommendations
            ]
        }
        
        return JsonResponse(data)
        
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


def generate_realistic_trend_score(product):
    """Generate realistic trend score based on product characteristics"""
    import random
    from datetime import datetime
    
    base_score = 5.0  # Start with neutral
    
    # Category-based trends
    category_lower = product.category.lower()
    if 'electronics' in category_lower or 'electronic' in category_lower:
        base_score += random.uniform(1.0, 3.0)  # Electronics generally high demand
    elif 'food' in category_lower:
        base_score += random.uniform(0.5, 2.0)  # Food moderate demand
    elif 'furniture' in category_lower:
        base_score += random.uniform(-1.0, 1.0)  # Furniture variable
    elif 'stationery' in category_lower:
        base_score += random.uniform(0.0, 1.5)  # Stationery steady
    else:
        base_score += random.uniform(-0.5, 1.5)  # Other categories
    
    # Stock level impact (low stock can indicate high demand)
    if product.total_stock < 50:
        base_score += random.uniform(1.0, 2.5)  # Low stock = high demand
    elif product.total_stock > 200:
        base_score += random.uniform(-1.5, 0.5)  # High stock = lower demand
    else:
        base_score += random.uniform(-0.5, 1.0)  # Normal stock
    
    # ABC Classification impact (based on current trend score)
    calculated_abc = product.calculated_abc_classification
    if calculated_abc == 'A':
        base_score += random.uniform(0.5, 1.5)  # A-class items higher demand
    elif calculated_abc == 'C':
        base_score += random.uniform(-1.0, 0.5)  # C-class items lower demand
    
    # Seasonal factors
    current_month = datetime.now().month
    if current_month in [11, 12, 1]:  # Winter/Holiday season
        base_score += random.uniform(0.5, 2.0)
    elif current_month in [6, 7, 8]:  # Summer
        if 'electronics' in category_lower:
            base_score += random.uniform(0.5, 1.5)  # AC, fans etc.
    
    # Add some randomness for market volatility
    base_score += random.uniform(-1.0, 1.0)
    
    # Ensure score is within bounds
    final_score = min(10.0, max(0.0, base_score))
    
    return round(final_score, 1)


def enhanced_simulation_ajax_update(request, products):
    """AJAX version of enhanced simulation when AI is not available"""
    import random
    from datetime import datetime
    from django.utils import timezone
    
    start_time = timezone.now()
    print(f"--- Starting AJAX Enhanced Simulation Update at {start_time.strftime('%H:%M:%S')} ---")
    updated_count = 0
    
    for product in products:
        current_time = timezone.now().strftime('%H:%M:%S')
        print(f"[{current_time}] Updating product: {product.name}")
        
        # Enhanced simulation logic
        base_score = product.trend_score
        old_score = base_score
        
        # Factor 1: Stock level impact
        stock_factor = 0
        if product.total_stock < 50:
            stock_factor = random.uniform(0.5, 1.5)
        elif product.total_stock > 200:
            stock_factor = random.uniform(-1.0, -0.2)
        else:
            stock_factor = random.uniform(-0.3, 0.3)
        
        # Factor 2: ABC classification impact (based on current trend score)
        abc_factor = 0
        calculated_abc = product.calculated_abc_classification
        if calculated_abc == 'A':
            abc_factor = random.uniform(0.2, 0.8)
        elif calculated_abc == 'B':
            abc_factor = random.uniform(-0.2, 0.4)
        else:
            abc_factor = random.uniform(-0.5, 0.2)
        
        # Factor 3: Category-based trends
        category_factor = 0
        if 'Electronics' in product.category:
            category_factor = random.uniform(0.3, 1.0)
        elif 'Food' in product.category:
            category_factor = random.uniform(-0.2, 0.5)
        else:
            category_factor = random.uniform(-0.3, 0.3)
        
        # Factor 4: Seasonal simulation
        current_month = datetime.now().month
        seasonal_factor = 0
        if current_month in [11, 12, 1]:
            seasonal_factor = random.uniform(0.5, 1.2)
        elif current_month in [6, 7, 8]:
            seasonal_factor = random.uniform(-0.2, 0.6)
        else:
            seasonal_factor = random.uniform(-0.3, 0.3)
        
        # Calculate new trend score
        trend_change = stock_factor + abc_factor + category_factor + seasonal_factor
        new_score = base_score + trend_change
        final_score = min(10.0, max(0.0, new_score + random.uniform(-0.5, 0.5)))
        
        # Update the product with explicit timestamp
        product.trend_score = round(final_score, 1)
        product.last_trend_update = timezone.now()  # Exact current time
        product.save(update_fields=['trend_score', 'last_trend_update'])
        
        update_time = product.last_trend_update.strftime('%H:%M:%S')
        print(f"   -> Updated: {product.name} | Old: {old_score} -> New: {product.trend_score} | Time: {update_time}")
        updated_count += 1
    
    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"--- AJAX Simulation Complete! Updated {updated_count} products in {duration:.1f} seconds ---")
    
    # Get updated data for response
    updated_products = Product.objects.all()
    
    # Calculate updated KPI data
    high_demand = updated_products.filter(trend_score__gte=7).count()
    low_demand = updated_products.filter(trend_score__lt=4).count()
    price_actions_count = 0
    for product in updated_products:
        if (product.trend_score >= 7 and product.total_stock >= 100) or \
           (product.trend_score < 3 and product.total_stock > 150):
            price_actions_count += 1
    
    # Get the most recent update time
    latest_update = updated_products.filter(last_trend_update__isnull=False).order_by('-last_trend_update').first()
    
    # Prepare product data for JSON response
    products_data = []
    for product in updated_products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'total_stock': product.total_stock,
            'trend_score': float(product.trend_score),
            'last_trend_update': product.last_trend_update.isoformat() if product.last_trend_update else None,
        })
    
    return JsonResponse({
        'success': True,
        'message': f'✅ Enhanced Simulation Complete! Updated {updated_count} products with market analysis. Completed at {end_time.strftime("%H:%M:%S")} (Duration: {duration:.1f}s)',
        'products': products_data,
        'kpi_data': {
            'high_demand_count': high_demand,
            'low_demand_count': low_demand,
            'price_actions_count': price_actions_count,
        },
        'last_updated': latest_update.last_trend_update.isoformat() if latest_update else None,
    })


def enhanced_simulation_update(request, products):
    """Fallback enhanced simulation when AI is not available"""
    import random
    from datetime import datetime
    from django.utils import timezone
    
    start_time = timezone.now()
    print(f"--- Starting Enhanced Simulation Update at {start_time.strftime('%H:%M:%S')} ---")
    updated_count = 0
    
    for product in products:
        current_time = timezone.now().strftime('%H:%M:%S')
        print(f"[{current_time}] Updating product: {product.name}")
        
        # Enhanced simulation logic
        base_score = product.trend_score
        old_score = base_score
        
        # Factor 1: Stock level impact
        stock_factor = 0
        if product.total_stock < 50:
            stock_factor = random.uniform(0.5, 1.5)
        elif product.total_stock > 200:
            stock_factor = random.uniform(-1.0, -0.2)
        else:
            stock_factor = random.uniform(-0.3, 0.3)
        
        # Factor 2: ABC classification impact (based on current trend score)
        abc_factor = 0
        calculated_abc = product.calculated_abc_classification
        if calculated_abc == 'A':
            abc_factor = random.uniform(0.2, 0.8)
        elif calculated_abc == 'B':
            abc_factor = random.uniform(-0.2, 0.4)
        else:
            abc_factor = random.uniform(-0.5, 0.2)
        
        # Factor 3: Category-based trends
        category_factor = 0
        if 'Electronics' in product.category:
            category_factor = random.uniform(0.3, 1.0)
        elif 'Food' in product.category:
            category_factor = random.uniform(-0.2, 0.5)
        else:
            category_factor = random.uniform(-0.3, 0.3)
        
        # Factor 4: Seasonal simulation
        current_month = datetime.now().month
        seasonal_factor = 0
        if current_month in [11, 12, 1]:
            seasonal_factor = random.uniform(0.5, 1.2)
        elif current_month in [6, 7, 8]:
            seasonal_factor = random.uniform(-0.2, 0.6)
        else:
            seasonal_factor = random.uniform(-0.3, 0.3)
        
        # Calculate new trend score
        trend_change = stock_factor + abc_factor + category_factor + seasonal_factor
        new_score = base_score + trend_change
        final_score = min(10.0, max(0.0, new_score + random.uniform(-0.5, 0.5)))
        
        # Update the product with explicit timestamp
        product.trend_score = round(final_score, 1)
        product.last_trend_update = timezone.now()  # Exact current time
        product.save(update_fields=['trend_score', 'last_trend_update'])
        
        update_time = product.last_trend_update.strftime('%H:%M:%S')
        print(f"   -> Updated: {product.name} | Old: {old_score} -> New: {product.trend_score} | Time: {update_time}")
        updated_count += 1
    
    end_time = timezone.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"--- Simulation Complete! Updated {updated_count} products in {duration:.1f} seconds ---")
    messages.success(request, f'✅ Enhanced Simulation Complete! Updated {updated_count} products with market analysis. Completed at {end_time.strftime("%H:%M:%S")} (Duration: {duration:.1f}s)')
    return redirect('trend_dashboard')

@login_required
def admin_dashboard(request):
    products = Product.objects.all()
    
    # Stock intelligence analysis
    stock_analysis = []
    for product in products:
        total_stock = product.total_stock
        days_to_expiry = product.days_to_nearest_expiry
        
        condition = "Normal"
        if total_stock > 100 and product.trend_score < 3:
            condition = "Overstock"
        elif total_stock < 10:
            condition = "Reorder needed"
        elif days_to_expiry and days_to_expiry < 15:
            condition = "Near expiry"
        elif days_to_expiry and days_to_expiry < 0:
            condition = "Expired"
        
        stock_analysis.append({
            'product': product,
            'total_stock': total_stock,
            'days_to_expiry': days_to_expiry,
            'condition': condition
        })
    
    # Get sent notifications (admin messages only) - get full queryset first
    try:
        sent_notifications_queryset = Notification.objects.filter(
            notification_type='admin_message'
        ).order_by('-created_at')
    except Exception as e:
        # Fallback if there are any database issues
        sent_notifications_queryset = Notification.objects.none()
        print(f"DEBUG: Error querying notifications: {e}")
    
    # Count notification statistics (before slicing)
    total_sent = sent_notifications_queryset.count()
    unread_notifications = sent_notifications_queryset.filter(is_read=False).count()
    read_notifications = sent_notifications_queryset.filter(is_read=True).count()
    
    # Now slice for display (limit to 20)
    sent_notifications = sent_notifications_queryset[:20]
    
    if request.method == 'POST':
        if 'apply_discount' in request.POST:
            discount_form = DiscountForm(request.POST)
            
            if discount_form.is_valid():
                product = discount_form.cleaned_data['product']
                discount = discount_form.cleaned_data['discount_percentage']
                
                from decimal import Decimal
                
                # Store old values for comparison
                old_price = product.new_price
                old_discount = product.discount_percentage
                
                # Apply discount
                product.discount_percentage = discount
                product.new_price = product.selling_price * (Decimal('1') - Decimal(str(discount)) / Decimal('100'))
                product.save()
                
                messages.success(request, f'✅ Discount applied to {product.name}! Price changed from ₹{old_price} to ₹{product.new_price} ({discount}% discount)')
                return redirect('admin_dashboard')
            else:
                # Show form errors
                for field, errors in discount_form.errors.items():
                    for error in errors:
                        messages.error(request, f'Discount form error in {field}: {error}')
                messages.error(request, 'Please check the discount form and try again.')
        
        elif 'delete_notification' in request.POST:
            notification_id = request.POST.get('notification_id')
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id)
                    notification_title = notification.title
                    notification.delete()
                    messages.success(request, f'✅ Notification "{notification_title}" deleted successfully!')
                    return redirect('admin_dashboard')
                except Notification.DoesNotExist:
                    messages.error(request, '❌ Notification not found!')
                except Exception as e:
                    messages.error(request, f'❌ Error deleting notification: {str(e)}')
            else:
                messages.error(request, '❌ No notification ID provided!')
        
        elif 'send_notification' in request.POST:
            print("DEBUG: Send notification form submitted")
            print(f"DEBUG: All POST data: {dict(request.POST)}")
            
            # Get form data
            product_name = request.POST.get('product_name')
            product_category = request.POST.get('product_category')
            title = request.POST.get('notification_title')
            admin_recommendation = request.POST.get('admin_recommendation')
            notification_type = request.POST.get('notification_type', 'admin_message')
            priority = request.POST.get('notification_priority', 'medium')
            
            print(f"DEBUG: Extracted data:")
            print(f"  - Product Name: '{product_name}'")
            print(f"  - Product Category: '{product_category}'")
            print(f"  - Title: '{title}'")
            print(f"  - Recommendation: '{admin_recommendation}'")
            print(f"  - Type: '{notification_type}'")
            print(f"  - Priority: '{priority}'")
            
            # Check if all required fields are present
            required_fields = [product_name, product_category, title, admin_recommendation]
            missing_fields = [field for field in required_fields if not field or not field.strip()]
            
            if not missing_fields:
                print("DEBUG: All required fields present, creating notification...")
                try:
                    # Try to find the product in database
                    product = None
                    current_stock = 0
                    trend_score = 0.0
                    
                    try:
                        # Look for exact or partial match
                        product = Product.objects.filter(name__icontains=product_name).first()
                        if product:
                            current_stock = product.total_stock
                            trend_score = product.trend_score
                            print(f"DEBUG: Found matching product: {product.name}")
                        else:
                            print(f"DEBUG: No matching product found for: {product_name}")
                    except Exception as e:
                        print(f"DEBUG: Error finding product: {e}")
                    
                    # Get current time
                    current_time = timezone.now()
                    formatted_time = current_time.strftime('%B %d, %Y at %I:%M %p')
                    
                    # Create detailed message with all information
                    detailed_message = f"""Product Details:
• Name: {product_name}
• Category: {product_category}
• Current Stock: {current_stock} units
• Trend Score: {trend_score}/10

Admin Recommendation:
{admin_recommendation}

Notification Details:
• Priority: {priority.upper()}
• Sent: {formatted_time}
• From: Admin ({request.user.username})"""
                    
                    print(f"DEBUG: Creating notification with:")
                    print(f"  - Title: '{title}'")
                    print(f"  - Target Role: 'inventory'")
                    print(f"  - Type: '{notification_type}'")
                    print(f"  - Priority: '{priority}'")
                    print(f"  - Product: {product}")
                    
                    # Create notification for inventory team
                    notification = Notification.objects.create(
                        title=f"{title}",
                        message=detailed_message,
                        notification_type=notification_type,
                        priority=priority,
                        target_user_role='inventory',
                        product=product,
                        is_read=False
                    )
                    
                    print(f"DEBUG: Notification created successfully!")
                    print(f"  - ID: {notification.id}")
                    print(f"  - Title: {notification.title}")
                    print(f"  - Target Role: {notification.target_user_role}")
                    print(f"  - Is Read: {notification.is_read}")
                    print(f"  - Created At: {notification.created_at}")
                    
                    # Verify it can be found in inventory query
                    inventory_check = Notification.objects.filter(
                        target_user_role__in=['inventory', 'all'],
                        is_read=False,
                        id=notification.id
                    ).exists()
                    print(f"DEBUG: Notification found in inventory query: {inventory_check}")
                    
                    success_message = f'✅ Detailed notification sent to inventory team!'
                    
                    messages.success(request, success_message)
                    print(f"DEBUG: Success message added, redirecting...")
                    return redirect('admin_dashboard')
                    
                except Exception as e:
                    print(f"DEBUG: Error creating notification: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f'❌ Error sending notification: {str(e)}')
            else:
                print(f"DEBUG: Missing required fields: {missing_fields}")
                messages.error(request, '⚠️ Please fill in all required fields: Product Name, Category, Title, and Recommendation.')
    
    discount_form = DiscountForm()
    
    # If there were form errors, rebind the form with POST data
    if request.method == 'POST' and 'apply_discount' in request.POST:
        discount_form = DiscountForm(request.POST)
    
    orders = OrderQueue.objects.all().order_by('-created_at')
    
    # Count different order statuses
    pending_orders_count = OrderQueue.objects.filter(status='pending').count()
    ordered_count = OrderQueue.objects.filter(status='ordered').count()
    received_count = OrderQueue.objects.filter(status='received').count()
    
    # Count conditions for dashboard stats
    overstock_count = sum(1 for item in stock_analysis if item['condition'] == 'Overstock')
    reorder_count = sum(1 for item in stock_analysis if item['condition'] == 'Reorder needed')
    near_expiry_count = sum(1 for item in stock_analysis if item['condition'] == 'Near expiry')
    expired_count = sum(1 for item in stock_analysis if item['condition'] == 'Expired')
    
    context = {
        'stock_analysis': stock_analysis,
        'discount_form': discount_form,
        'orders': orders,
        'sent_notifications': sent_notifications,
        'total_sent': total_sent,
        'unread_notifications': unread_notifications,
        'read_notifications': read_notifications,
        'overstock_count': overstock_count,
        'reorder_count': reorder_count,
        'near_expiry_count': near_expiry_count,
        'expired_count': expired_count,
        'pending_orders_count': pending_orders_count,
        'ordered_count': ordered_count,
        'received_count': received_count,
        'products': Product.objects.all(),  # Add products for notification form
        'products_json': json.dumps([{
            'name': product.name,
            'category': product.category,
            'stock': product.total_stock,
            'trendScore': float(product.trend_score)
        } for product in Product.objects.all()]),
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
def create_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order created successfully!')
    return redirect('admin_dashboard')

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(OrderQueue, id=order_id)
    new_status = request.POST.get('status')
    
    if new_status in ['pending', 'ordered', 'received']:
        order.status = new_status
        order.save()
        
        if new_status == 'received':
            # Add stock when order is received
            ExpiryStock.objects.create(
                product=order.product,
                quantity=order.quantity,
                expiry_date=date.today() + timedelta(days=365)  # Default 1 year expiry
            )
            messages.success(request, f'Order received and stock updated for {order.product.name}!')
    
    return redirect('admin_dashboard')

@login_required
def billing(request):
    if request.method == 'POST':
        sales_form = SalesForm(request.POST)
        if sales_form.is_valid():
            product = sales_form.cleaned_data['product']
            quantity = sales_form.cleaned_data['quantity']
            
            # Check available non-expired stock only
            available_stock = product.total_stock  # This now excludes expired stock
            
            if available_stock >= quantity:
                from decimal import Decimal
                
                # Create bill
                bill = SalesBill.objects.create(
                    bill_number=f"BILL-{SalesBill.objects.count() + 1:06d}",
                    total_amount=product.new_price * Decimal(str(quantity))
                )
                
                # Create bill item
                SalesBillItem.objects.create(
                    bill=bill,
                    product=product,
                    quantity=quantity,
                    price=product.new_price,
                    total=product.new_price * Decimal(str(quantity))
                )
                
                # FEFO stock deduction (only from non-expired stock)
                remaining_qty = quantity
                from datetime import date
                stock_batches = product.expirystock_set.filter(
                    quantity__gt=0,
                    expiry_date__gte=date.today()  # Only non-expired stock
                ).order_by('expiry_date')
                
                for batch in stock_batches:
                    if remaining_qty <= 0:
                        break
                    
                    if batch.quantity >= remaining_qty:
                        batch.quantity -= remaining_qty
                        remaining_qty = 0
                    else:
                        remaining_qty -= batch.quantity
                        batch.quantity = 0
                    
                    batch.save()
                
                messages.success(request, f'Sale completed! Bill #{bill.bill_number}')
                return redirect('billing')
            else:
                messages.error(request, f'Insufficient stock! Available: {available_stock} units (expired stock excluded)')
    
    sales_form = SalesForm()
    recent_bills = SalesBill.objects.prefetch_related('items__product').order_by('-created_at')[:10]
    
    # Calculate today's sales properly
    from datetime import date
    from django.db.models import Sum
    
    today = date.today()
    today_bills = SalesBill.objects.filter(created_at__date=today)
    today_sales_count = today_bills.count()
    today_sales_amount = today_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Calculate current month's sales
    current_month = today.month
    current_year = today.year
    monthly_bills = SalesBill.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month
    )
    monthly_sales_count = monthly_bills.count()
    monthly_sales_amount = monthly_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'sales_form': sales_form,
        'recent_bills': recent_bills,
        'today_sales_count': today_sales_count,
        'today_sales_amount': today_sales_amount,
        'monthly_sales_count': monthly_sales_count,
        'monthly_sales_amount': monthly_sales_amount,
        'current_month_name': today.strftime('%B %Y'),  # e.g., "February 2026"
    }
    return render(request, 'billing.html', context)

@login_required
def get_bill_details(request, bill_id):
    """AJAX endpoint to get bill details"""
    try:
        bill = SalesBill.objects.prefetch_related('items__product').get(id=bill_id)
        bill_data = {
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.strftime('%b %d, %Y %H:%M'),
            'total_amount': str(bill.total_amount),
            'items': []
        }
        
        for item in bill.items.all():
            bill_data['items'].append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': str(item.price),
                'total': str(item.total)
            })
        
        return JsonResponse(bill_data)
    except SalesBill.DoesNotExist:
        return JsonResponse({'error': 'Bill not found'}, status=404)

@login_required
def get_product_details(request, product_id):
    """AJAX endpoint to get product stock details"""
    try:
        product = Product.objects.get(id=product_id)
        from datetime import date
        
        # Only get non-expired stock batches
        stock_batches = product.expirystock_set.filter(
            quantity__gt=0,
            expiry_date__gte=date.today()  # Only non-expired stock
        ).order_by('expiry_date')
        
        batches_data = []
        for batch in stock_batches:
            days_to_expiry = (batch.expiry_date - date.today()).days
            batches_data.append({
                'quantity': batch.quantity,
                'expiry_date': batch.expiry_date.strftime('%b %d, %Y'),
                'days_to_expiry': days_to_expiry
            })
        
        # Check if there's expired stock
        expired_stock = product.expired_stock
        
        product_data = {
            'name': product.name,
            'category': product.category,
            'total_stock': product.total_stock,  # This now excludes expired stock
            'expired_stock': expired_stock,
            'current_price': str(product.new_price),
            'selling_price': str(product.selling_price),
            'cost_price': str(product.cost_price),
            'abc_classification': product.calculated_abc_classification,
            'trend_score': float(product.trend_score),
            'batches': batches_data
        }
        
        return JsonResponse(product_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        from django.utils import timezone
        notification = Notification.objects.get(id=notification_id)
        notification.is_read = True
        notification.updated_at = timezone.now()
        notification.save(update_fields=['is_read', 'updated_at'])
        return JsonResponse({'success': True})
    except Notification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})

@login_required
def search_products(request):
    """AJAX endpoint for product autocomplete search"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'products': []})
    
    # Search products by name (case-insensitive, starts with or contains)
    products = Product.objects.filter(
        name__icontains=query
    ).order_by('name')[:10]  # Limit to 10 results
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'stock': product.total_stock,
            'price': str(product.new_price),
            'display_text': f"{product.name} - {product.category} (Stock: {product.total_stock})"
        })
    
    return JsonResponse({'products': product_list})

@login_required
def apply_recommendation(request):
    """Apply AI recommendation for a product"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Determine the recommendation based on trend score and stock
            recommendation_applied = ""
            
            if product.trend_score >= 7 and product.total_stock < 100:
                # High demand, low stock - Increase stock recommendation
                recommendation_applied = "Increase Stock recommendation noted"
                
                # Create AI recommendation record
                if AIRecommendation:
                    AIRecommendation.objects.update_or_create(
                        product=product,
                        recommendation_type='increase_stock',
                        status='pending',
                        defaults={
                            'recommendation_text': f'Increase stock for {product.name} due to high demand',
                            'trend_score': product.trend_score,
                            'stock_level': product.total_stock,
                            'suggested_quantity': max(200, product.total_stock * 2),
                            'applied_by': request.user.username,
                            'applied_at': timezone.now(),
                            'status': 'applied'
                        }
                    )
                
            elif product.trend_score >= 7 and product.total_stock >= 100:
                # High demand, good stock - Raise price
                from decimal import Decimal
                old_price = product.new_price
                new_price = old_price * Decimal('1.10')  # 10% increase
                product.new_price = new_price
                product.save(update_fields=['new_price'])
                
                recommendation_applied = f"Price raised from ₹{old_price} to ₹{new_price} (10% increase)"
                
                # Create AI recommendation record
                if AIRecommendation:
                    AIRecommendation.objects.update_or_create(
                        product=product,
                        recommendation_type='raise_price',
                        status='pending',
                        defaults={
                            'recommendation_text': f'Raise price for {product.name} due to high demand',
                            'trend_score': product.trend_score,
                            'stock_level': product.total_stock,
                            'suggested_value': new_price,
                            'applied_by': request.user.username,
                            'applied_at': timezone.now(),
                            'status': 'applied'
                        }
                    )
                
            elif product.trend_score < 3 and product.total_stock > 150:
                # Low demand, overstock - Apply discount
                from decimal import Decimal
                old_price = product.new_price
                discount_percent = 15  # 15% discount
                new_price = old_price * (Decimal('1') - Decimal(str(discount_percent)) / Decimal('100'))
                product.new_price = new_price
                product.discount_percentage = discount_percent
                product.save(update_fields=['new_price', 'discount_percentage'])
                
                recommendation_applied = f"Discount applied: {discount_percent}% off. Price reduced from ₹{old_price} to ₹{new_price}"
                
                # Create AI recommendation record
                if AIRecommendation:
                    AIRecommendation.objects.update_or_create(
                        product=product,
                        recommendation_type='apply_discount',
                        status='pending',
                        defaults={
                            'recommendation_text': f'Apply discount for {product.name} due to low demand and overstock',
                            'trend_score': product.trend_score,
                            'stock_level': product.total_stock,
                            'suggested_value': Decimal(str(discount_percent)),
                            'applied_by': request.user.username,
                            'applied_at': timezone.now(),
                            'status': 'applied'
                        }
                    )
                
            elif product.trend_score < 3:
                # Low demand - Reduce orders
                recommendation_applied = "Reduce orders recommendation noted for low demand product"
                
                # Create AI recommendation record
                if AIRecommendation:
                    AIRecommendation.objects.update_or_create(
                        product=product,
                        recommendation_type='reduce_orders',
                        status='pending',
                        defaults={
                            'recommendation_text': f'Reduce future orders for {product.name} due to low demand',
                            'trend_score': product.trend_score,
                            'stock_level': product.total_stock,
                            'applied_by': request.user.username,
                            'applied_at': timezone.now(),
                            'status': 'applied'
                        }
                    )
                
            elif product.total_stock < 50:
                # Low stock - Reorder soon
                recommendation_applied = "Reorder recommendation noted for low stock product"
                
                # Create AI recommendation record
                if AIRecommendation:
                    AIRecommendation.objects.update_or_create(
                        product=product,
                        recommendation_type='reorder_soon',
                        status='pending',
                        defaults={
                            'recommendation_text': f'Reorder {product.name} soon due to low stock',
                            'trend_score': product.trend_score,
                            'stock_level': product.total_stock,
                            'suggested_quantity': max(100, product.total_stock * 3),
                            'applied_by': request.user.username,
                            'applied_at': timezone.now(),
                            'status': 'applied'
                        }
                    )
                
            else:
                # Monitor - No specific action
                recommendation_applied = "Product marked for monitoring"
                
                # Create AI recommendation record
                if AIRecommendation:
                    AIRecommendation.objects.update_or_create(
                        product=product,
                        recommendation_type='monitor',
                        status='pending',
                        defaults={
                            'recommendation_text': f'Continue monitoring {product.name} - stable conditions',
                            'trend_score': product.trend_score,
                            'stock_level': product.total_stock,
                            'applied_by': request.user.username,
                            'applied_at': timezone.now(),
                            'status': 'applied'
                        }
                    )
            
            return JsonResponse({
                'success': True,
                'message': f'Recommendation applied for {product.name}: {recommendation_applied}'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error applying recommendation: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def dismiss_recommendation(request):
    """Dismiss AI recommendation for a product"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        
        try:
            product = Product.objects.get(id=product_id)
            
            # Create dismissed recommendation record
            if AIRecommendation:
                # Mark any pending recommendations as dismissed
                pending_recommendations = AIRecommendation.objects.filter(
                    product=product,
                    status='pending'
                )
                
                for rec in pending_recommendations:
                    rec.status = 'dismissed'
                    rec.applied_by = request.user.username
                    rec.applied_at = timezone.now()
                    rec.save()
                
                # Create a new dismissed record
                AIRecommendation.objects.create(
                    product=product,
                    recommendation_type='monitor',
                    recommendation_text=f'AI recommendations dismissed for {product.name} by user',
                    trend_score=product.trend_score,
                    stock_level=product.total_stock,
                    status='dismissed',
                    applied_by=request.user.username,
                    applied_at=timezone.now()
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Recommendations dismissed for {product.name}'
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Product not found'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error dismissing recommendation: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})