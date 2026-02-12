from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, F, Q
from django.db import models
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

def get_next_bill_number():
    """Generate the next sequential bill number for both single and multi-product bills"""
    # Get all bills with BILL- format to find the highest number
    bills_with_standard_format = SalesBill.objects.filter(
        bill_number__startswith='BILL-'
    ).order_by('-bill_number')
    
    if bills_with_standard_format.exists():
        # Extract the highest number from BILL-XXXXXX format
        try:
            latest_standard_bill = bills_with_standard_format.first()
            last_number = int(latest_standard_bill.bill_number.split('-')[1])
            next_number = last_number + 1
        except (ValueError, IndexError):
            # Fallback to counting all bills + 1
            next_number = SalesBill.objects.count() + 1
    else:
        # No standard format bills exist, start from 1
        next_number = 1
    
    return f"BILL-{next_number:06d}"

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

def update_stock_notifications_for_product(product):
    """Update stock notifications for a specific product when stock changes"""
    from datetime import date
    
    # Refresh product data from database
    product.refresh_from_db()
    current_stock = product.total_stock
    
    # Remove existing stock notifications for this product
    Notification.objects.filter(
        product=product,
        notification_type='low_stock'
    ).delete()
    
    # Create new notification if stock is low
    if current_stock < 20:  # Low stock threshold
        # Get detailed stock information
        valid_batches = product.expirystock_set.filter(
            quantity__gt=0,
            expiry_date__gte=date.today()
        )
        
        # Create detailed stock breakdown
        stock_details = []
        for batch in valid_batches:
            days_to_expiry = (batch.expiry_date - date.today()).days
            stock_details.append(f"• {batch.quantity} units (expires in {days_to_expiry} days)")
        
        stock_breakdown = "\n".join(stock_details) if stock_details else "No valid stock available"
        
        if current_stock == 0:
            priority = 'urgent'
            title = f"🚨 OUT OF STOCK: {product.name}"
            action_message = "IMMEDIATE ACTION REQUIRED: Product is completely out of stock!"
        elif current_stock < 5:
            priority = 'high'
            title = f"⚠️ CRITICAL LOW: {product.name} ({current_stock} units)"
            action_message = "URGENT: Stock is critically low!"
        else:
            priority = 'medium'
            title = f"📦 Low Stock: {product.name} ({current_stock} units)"
            action_message = "Consider reordering soon to avoid stockout"
        
        message = f"Product: {product.name}\nCurrent Stock: {current_stock} units\n\nStock Breakdown:\n{stock_breakdown}\n\n{action_message}\nRecommendation: Reorder immediately to maintain adequate inventory levels"
        
        Notification.objects.create(
            title=title,
            message=message,
            notification_type='low_stock',
            priority=priority,
            target_user_role='inventory',
            product=product
        )

def generate_notifications():
    """Generate automatic notifications for inventory management with accurate stock quantities"""
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
    
    # Clear outdated stock notifications (older than 1 day) to prevent stale data
    outdated_stock_notifications = Notification.objects.filter(
        notification_type='low_stock',
        created_at__lt=timezone.now() - timedelta(days=1)
    )
    outdated_stock_notifications.delete()
    
    # Get all products with stock
    products = Product.objects.all()
    
    for product in products:
        # Get real-time stock quantity (refresh from database)
        product.refresh_from_db()
        current_stock = product.total_stock
        
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
        
        # Check for low stock warnings with accurate current stock
        if current_stock < 20:  # Low stock threshold
            existing_low_stock = Notification.objects.filter(
                product=product,
                notification_type='low_stock',
                created_at__date=date.today()
            ).exists()
            
            if not existing_low_stock:
                # Get detailed stock information for accurate reporting
                valid_batches = product.expirystock_set.filter(
                    quantity__gt=0,
                    expiry_date__gte=date.today()
                )
                
                # Create detailed stock breakdown
                stock_details = []
                for batch in valid_batches:
                    days_to_expiry = (batch.expiry_date - date.today()).days
                    stock_details.append(f"• {batch.quantity} units (expires in {days_to_expiry} days)")
                
                stock_breakdown = "\n".join(stock_details) if stock_details else "No valid stock available"
                
                if current_stock == 0:
                    priority = 'urgent'
                    title = f"🚨 OUT OF STOCK: {product.name}"
                    action_message = "IMMEDIATE ACTION REQUIRED: Product is completely out of stock!"
                elif current_stock < 5:
                    priority = 'high'
                    title = f"⚠️ CRITICAL LOW: {product.name} ({current_stock} units)"
                    action_message = "URGENT: Stock is critically low!"
                else:
                    priority = 'medium'
                    title = f"📦 Low Stock: {product.name} ({current_stock} units)"
                    action_message = "Consider reordering soon to avoid stockout"
                
                message = f"Product: {product.name}\nCurrent Stock: {current_stock} units\n\nStock Breakdown:\n{stock_breakdown}\n\n{action_message}\nRecommendation: Reorder immediately to maintain adequate inventory levels"
                
                Notification.objects.create(
                    title=title,
                    message=message,
                    notification_type='low_stock',
                    priority=priority,
                    target_user_role='inventory',
                    product=product
                )

def user_login(request):
    # If user is already logged in, redirect to their dashboard
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            if profile.role == 'inventory':
                return redirect('inventory_dashboard')
            elif profile.role == 'marketing':
                return redirect('trend_dashboard')
            elif profile.role == 'admin':
                return redirect('admin_dashboard')
        except UserProfile.DoesNotExist:
            return redirect('inventory_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me')  # Check if remember me is checked
        
        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'login.html')
        
        # Authenticate using username and password
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Set session expiry based on remember me checkbox
            if remember_me:
                # Remember for 30 days
                request.session.set_expiry(60 * 60 * 24 * 30)
            else:
                # Remember until browser closes (but still keep for 7 days minimum)
                request.session.set_expiry(60 * 60 * 24 * 7)
            
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
    # If user is already logged in, redirect to their dashboard
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            if profile.role == 'inventory':
                return redirect('inventory_dashboard')
            elif profile.role == 'marketing':
                return redirect('trend_dashboard')
            elif profile.role == 'admin':
                return redirect('admin_dashboard')
        except UserProfile.DoesNotExist:
            return redirect('inventory_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        role = request.POST.get('role', '').strip()
        store_name = request.POST.get('store_name', '').strip()
        store_location = request.POST.get('store_location', '').strip()
        
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
            profile = UserProfile.objects.create(
                user=user,
                role=role,
                store_name=store_name if store_name else None,
                store_location=store_location if store_location else None
            )
            
            # Auto-login the new user
            login(request, user)
            
            # Set persistent session for new users (30 days by default)
            request.session.set_expiry(60 * 60 * 24 * 30)
            
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
    # Check if user has a profile
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, '❌ Your account does not have a user profile. Please contact admin or create a new account through signup.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    # Generate notifications first
    generate_notifications()
    
    products = Product.objects.all()
    # Show only current user's stock in recent stock
    recent_stock = ExpiryStock.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get unread notifications for inventory role with proper priority ordering
    # Prioritize admin messages first, then by priority, then by creation date
    from django.db.models import Case, When, IntegerField
    
    notifications_queryset = Notification.objects.filter(
        target_user_role__in=['inventory', 'all'],
        is_read=False
    ).annotate(
        priority_order=Case(
            When(priority='urgent', then=4),
            When(priority='high', then=3),
            When(priority='medium', then=2),
            When(priority='low', then=1),
            default=0,
            output_field=IntegerField()
        ),
        admin_priority=Case(
            When(notification_type='admin_message', then=1),
            default=0,
            output_field=IntegerField()
        )
    ).order_by('-admin_priority', '-priority_order', '-created_at')
    
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
                stock_entry = stock_form.save(commit=False)
                stock_entry.user = request.user  # Assign stock to current user
                stock_entry.save()
                
                # Update trend score automatically
                from inventory.trend_calculator import update_product_trend_score
                new_score = update_product_trend_score(stock_entry.product)
                
                # Check if there are pending orders for this product
                pending_orders = OrderQueue.objects.filter(
                    product=stock_entry.product,
                    status__in=['pending', 'ordered'],
                    message_received=True  # Only for acknowledged orders
                )
                
                # Notify admin about stock addition for ordered products
                for order in pending_orders:
                    if order.ordered_by:  # Make sure there's an admin who ordered it
                        Notification.objects.create(
                            title=f"📦 STOCK RECEIVED: {stock_entry.product.name}",
                            message=f"Inventory team has added stock for your order:\n\n"
                                   f"Product: {stock_entry.product.name}\n"
                                   f"Stock Added: {stock_entry.quantity} units\n"
                                   f"Expiry Date: {stock_entry.expiry_date.strftime('%B %d, %Y')}\n"
                                   f"New Total Stock: {stock_entry.product.total_stock} units\n"
                                   f"Added by: {request.user.first_name or request.user.username}\n"
                                   f"Added at: {timezone.now().strftime('%B %d, %Y at %H:%M')}\n\n"
                                   f"Original Order Details:\n"
                                   f"Requested Quantity: {order.quantity} units\n"
                                   f"Order Date: {order.created_at.strftime('%B %d, %Y')}\n"
                                   f"Order ID: #{order.id}\n\n"
                                   f"✅ Your order request has been fulfilled!",
                            notification_type='stock_received',
                            priority='medium',
                            target_user_role='admin',
                            product=stock_entry.product
                        )
                
                # Update stock notifications for the product
                update_stock_notifications_for_product(stock_entry.product)
                
                # Show success message with order context if applicable
                if pending_orders.exists():
                    order_count = pending_orders.count()
                    messages.success(request, f'✅ Stock added to your inventory! Admin has been notified about {order_count} pending order(s) for {stock_entry.product.name}.')
                else:
                    messages.success(request, f'✅ Stock added to your inventory successfully! You now have {stock_entry.product.get_user_stock(request.user)} units of {stock_entry.product.name}.')
                
                return redirect('inventory_dashboard')
        
        elif 'request_product' in request.POST:
            # Inventory user requesting product from admin
            product_id = request.POST.get('order_product')
            quantity = request.POST.get('order_quantity')
            
            if product_id and quantity:
                try:
                    product = Product.objects.get(id=product_id)
                    quantity = int(quantity)
                    
                    # Create order request
                    order_request = OrderQueue.objects.create(
                        product=product,
                        quantity=quantity,
                        requested_by=request.user,
                        status='pending'
                    )
                    
                    # Update trend score automatically
                    from inventory.trend_calculator import update_product_trend_score
                    new_score = update_product_trend_score(product)
                    
                    # Get user's store info
                    user_profile = request.user.userprofile
                    user_identity = user_profile.full_identity
                    
                    # Notify admin about the request
                    Notification.objects.create(
                        title=f"🛒 Product Request: {product.name}",
                        message=f"📍 From: {user_identity} | "
                               f"📦 Product: {product.name} ({product.category}) | "
                               f"🔢 Qty: {quantity} units | "
                               f"💰 Price: ₹{product.cost_price} (Cost) / ₹{product.selling_price} (Selling) | "
                               f"📋 Available: {product.total_stock} units | "
                               f"📅 {timezone.now().strftime('%d %b %Y, %H:%M')}",
                        notification_type='admin_message',
                        priority='high',
                        target_user_role='admin',
                        product=product
                    )
                    
                    messages.success(request, f'✅ Product request sent to admin! You requested {quantity} units of {product.name}. Admin will check availability and send you the approved quantity.')
                    return redirect('inventory_dashboard')
                    
                except Product.DoesNotExist:
                    messages.error(request, '❌ Product not found!')
                except ValueError:
                    messages.error(request, '❌ Invalid quantity!')
            else:
                messages.error(request, '❌ Please select a product and enter quantity!')
            
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
    
    # Add user-specific stock and product order data
    products_with_data = []
    for product in products:
        # Count only orders that were actually created by admin and are still pending/ordered
        pending_orders_count = OrderQueue.objects.filter(
            product=product,
            status__in=['pending', 'ordered'],
            ordered_by__isnull=False,  # Only admin-created orders
            message_received=True  # Only acknowledged orders
        ).count()
        
        # Get user-specific stock
        user_stock = product.get_user_stock(request.user)
        
        # Add to product object for template access
        product.user_stock = user_stock
        product.pending_orders_count = pending_orders_count
        
        products_with_data.append({
            'id': product.id,
            'name': product.name,
            'stock': product.total_stock,
            'user_stock': user_stock,
            'pending_orders': pending_orders_count
        })

    
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
        'products_with_data': products_with_data,
    }
    
    return render(request, 'inventory_dashboard.html', context)

@login_required
def trend_dashboard(request):
    # Check if user has a profile
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, '❌ Your account does not have a user profile. Please contact admin or create a new account through signup.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
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
    # Check if user has a profile
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, '❌ Your account does not have a user profile. Please contact admin or create a new account through signup.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    print(f"🔧 DEBUG: Admin dashboard accessed by user: {request.user.username}")
    print(f"🔧 DEBUG: Request method: {request.method}")
    print(f"🔧 DEBUG: POST data: {dict(request.POST) if request.method == 'POST' else 'N/A'}")
    
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
        print(f"🔧 DEBUG: Processing POST request...")
        
        if 'apply_discount' in request.POST:
            print(f"🔧 DEBUG: Apply discount form submitted")
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
            print(f"🔧 DEBUG: Delete notification form submitted")
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
            print("🔧 DEBUG: Send notification form submitted")
            print(f"🔧 DEBUG: All POST data: {dict(request.POST)}")
            
            # Get form data
            product_name = request.POST.get('product_name')
            product_category = request.POST.get('product_category')
            title = request.POST.get('notification_title')
            admin_recommendation = request.POST.get('admin_recommendation')
            notification_type = request.POST.get('notification_type', 'admin_message')
            priority = request.POST.get('notification_priority', 'medium')
            
            print(f"🔧 DEBUG: Extracted data:")
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
                print("🔧 DEBUG: All required fields present, creating notification...")
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
                            print(f"🔧 DEBUG: Found matching product: {product.name}")
                        else:
                            print(f"🔧 DEBUG: No matching product found for: {product_name}")
                    except Exception as e:
                        print(f"🔧 DEBUG: Error finding product: {e}")
                    
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
                    
                    print(f"🔧 DEBUG: Creating notification with:")
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
                    
                    print(f"🔧 DEBUG: Notification created successfully!")
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
                    print(f"🔧 DEBUG: Notification found in inventory query: {inventory_check}")
                    
                    success_message = f'✅ Detailed notification sent to inventory team!'
                    
                    messages.success(request, success_message)
                    print(f"🔧 DEBUG: Success message added, redirecting...")
                    return redirect('admin_dashboard')
                    
                except Exception as e:
                    print(f"🔧 DEBUG: Error creating notification: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f'❌ Error sending notification: {str(e)}')
            else:
                print(f"🔧 DEBUG: Missing required fields: {missing_fields}")
                messages.error(request, '⚠️ Please fill in all required fields: Product Name, Category, Title, and Recommendation.')
        
        elif 'approve_product_request' in request.POST:
            print(f"🔧 DEBUG: Approve product request form submitted")
            request_id = request.POST.get('request_id')
            approved_quantity = request.POST.get('approved_quantity')
            
            if request_id and approved_quantity:
                try:
                    order_request = OrderQueue.objects.get(id=request_id, status='pending')
                    approved_quantity = int(approved_quantity)
                    product = order_request.product
                    
                    # Check if enough stock is available in COMPANY warehouse
                    company_stock = product.get_company_stock()
                    if approved_quantity > company_stock:
                        messages.error(request, f'❌ Not enough stock in company warehouse! Available: {company_stock} units, Requested: {approved_quantity} units')
                        return redirect('admin_dashboard')
                    
                    # Update order request
                    order_request.approved_quantity = approved_quantity
                    order_request.status = 'approved'
                    order_request.save()
                    
                    # Generate bill automatically
                    from datetime import datetime
                    bill_number = f"BILL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    
                    # Create bill
                    bill = SalesBill.objects.create(
                        bill_number=bill_number,
                        created_by=order_request.requested_by,  # Bill for the inventory user who requested
                        total_amount=0  # Will be calculated
                    )
                    
                    # Add bill item
                    item_total = product.selling_price * approved_quantity
                    SalesBillItem.objects.create(
                        bill=bill,
                        product=product,
                        quantity=approved_quantity,
                        price=product.selling_price,
                        total=item_total
                    )
                    
                    # Update bill total
                    bill.total_amount = item_total
                    bill.save()
                    
                    # Link bill to order request
                    order_request.bill = bill
                    order_request.bill_generated = True
                    order_request.save()
                    
                    # Deduct stock from COMPANY warehouse using FEFO logic
                    try:
                        company_user = User.objects.get(username='company_stock')
                        remaining_quantity = approved_quantity
                        stock_entries = ExpiryStock.objects.filter(
                            product=product,
                            user=company_user,  # Only deduct from company stock
                            quantity__gt=0
                        ).order_by('expiry_date')
                        
                        for stock_entry in stock_entries:
                            if remaining_quantity <= 0:
                                break
                            
                            if stock_entry.quantity >= remaining_quantity:
                                stock_entry.quantity -= remaining_quantity
                                stock_entry.save()
                                remaining_quantity = 0
                            else:
                                remaining_quantity -= stock_entry.quantity
                                stock_entry.quantity = 0
                                stock_entry.save()
                        
                        if remaining_quantity > 0:
                            messages.warning(request, f'⚠️ Only {approved_quantity - remaining_quantity} units available in company warehouse. {remaining_quantity} units short!')
                    except User.DoesNotExist:
                        messages.error(request, '❌ Company stock user not found! Please run setup_company_stock.py')
                        return redirect('admin_dashboard')
                    
                    # Notify inventory user
                    Notification.objects.create(
                        title=f"✅ Request Approved: {product.name}",
                        message=f"📦 Product: {product.name} | "
                               f"🔢 Requested: {order_request.quantity} units | "
                               f"✅ Approved: {approved_quantity} units | "
                               f"💰 Amount: ₹{item_total} | "
                               f"📄 Bill: {bill_number} | "
                               f"📊 Your Stock: {product.get_user_stock(order_request.requested_by)} units | "
                               f"📅 {timezone.now().strftime('%d %b %Y, %H:%M')}",
                        notification_type='admin_message',
                        priority='high',
                        target_user_role='inventory',
                        product=product
                    )
                    
                    # Update trend score automatically
                    from inventory.trend_calculator import update_product_trend_score
                    new_score = update_product_trend_score(product)
                    
                    messages.success(request, f'✅ Product request approved! Sent {approved_quantity} units of {product.name}. Bill #{bill_number} generated automatically.')
                    return redirect('admin_dashboard')
                    
                except OrderQueue.DoesNotExist:
                    messages.error(request, '❌ Order request not found!')
                except ValueError:
                    messages.error(request, '❌ Invalid quantity!')
                except Exception as e:
                    messages.error(request, f'❌ Error approving request: {str(e)}')
            else:
                messages.error(request, '❌ Missing request ID or quantity!')
    
    discount_form = DiscountForm()
    
    # If there were form errors, rebind the form with POST data
    if request.method == 'POST' and 'apply_discount' in request.POST:
        discount_form = DiscountForm(request.POST)
    
    orders = OrderQueue.objects.all().order_by('-created_at')
    
    # Count different order statuses
    # Pending orders: Orders that admin needs to review (requested by inventory, status='pending')
    pending_orders_count = OrderQueue.objects.filter(
        status='pending',
        requested_by__isnull=False  # Requested by inventory users
    ).count()
    
    # Orders Placed: All orders that inventory has requested (all statuses)
    # This shows total orders placed by inventory team
    ordered_count = OrderQueue.objects.filter(
        requested_by__isnull=False  # All orders requested by inventory users
    ).count()
    
    # Completed Orders: Orders that admin has approved/processed (not pending or cancelled)
    # This shows how many orders admin has completed/fulfilled
    completed_orders_count = OrderQueue.objects.filter(
        requested_by__isnull=False,  # Orders from inventory
        status__in=['approved', 'partially_fulfilled', 'shipped', 'delivered', 'completed']  # Admin has taken action
    ).count()
    
    # Additional counts for detailed tracking
    actual_received_count = OrderQueue.objects.filter(status='delivered').count()
    admin_seen_count = OrderQueue.objects.filter(message_received=True).count()
    
    print(f"🔧 DEBUG: Order counts:")
    print(f"  - Pending (Waiting for Admin): {pending_orders_count}")
    print(f"  - Orders Placed (Total by Inventory): {ordered_count}")
    print(f"  - Completed Orders (Approved by Admin): {completed_orders_count}")
    print(f"  - Actually Delivered: {actual_received_count}")
    print(f"  - Admin Seen: {admin_seen_count}")
    
    # Count conditions for dashboard stats
    overstock_count = sum(1 for item in stock_analysis if item['condition'] == 'Overstock')
    reorder_count = sum(1 for item in stock_analysis if item['condition'] == 'Reorder needed')
    near_expiry_count = sum(1 for item in stock_analysis if item['condition'] == 'Near expiry')
    expired_count = sum(1 for item in stock_analysis if item['condition'] == 'Expired')
    
    print(f"🔧 DEBUG: Context data prepared:")
    print(f"  - Products: {len(products)}")
    print(f"  - Orders: {len(orders)}")
    print(f"  - Notifications: {len(sent_notifications)}")
    print(f"  - Pending Orders: {pending_orders_count}")
    
    # Team Management Data
    from datetime import datetime, timedelta
    
    # Get all inventory users
    inventory_users_queryset = UserProfile.objects.filter(role='inventory').select_related('user')
    
    # Prepare simplified team data
    team_data = []
    active_inventory_users = inventory_users_queryset.count()  # Just count all inventory users as active
    
    for profile in inventory_users_queryset:
        user = profile.user
        team_data.append({
            'user': user,
        })
    
    # Sort by join date (newest first)
    team_data.sort(key=lambda x: x['user'].date_joined, reverse=True)
    
    # Get product requests from inventory users (pending only)
    product_requests = OrderQueue.objects.filter(
        requested_by__isnull=False,  # Requested by inventory user
        status='pending'
    ).select_related('product', 'requested_by').order_by('-created_at')
    
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
        'received_count': completed_orders_count,  # Use completed count for main display
        'actual_received_count': actual_received_count,  # Actual received orders
        'completed_orders_count': completed_orders_count,  # Total completed orders
        'admin_seen_count': admin_seen_count,  # Admin seen count for breakdown
        'products': Product.objects.all(),  # Add products for notification form
        'products_json': json.dumps([{
            'name': product.name,
            'category': product.category,
            'stock': product.total_stock,
            'trendScore': float(product.trend_score)
        } for product in Product.objects.all()]),
        'orders_json': json.dumps([{
            'id': order.id,
            'product': {
                'name': order.product.name,
                'stock': order.product.total_stock
            },
            'quantity': order.quantity,
            'status': order.status,
            'message_received': order.message_received,
            'message_received_at': order.message_received_at.strftime('%B %d, %Y at %H:%M') if order.message_received_at else None,
            'created_at': order.created_at.strftime('%B %d, %Y at %H:%M'),
            'ordered_by': order.ordered_by.first_name or order.ordered_by.username if order.ordered_by else None,
            'order_notes': order.order_notes or '',
            'inventory_action': getattr(order, 'inventory_action', 'none'),
            'inventory_action_by': getattr(order, 'inventory_action_by', None) and (order.inventory_action_by.first_name or order.inventory_action_by.username) if hasattr(order, 'inventory_action_by') else None,
            'inventory_action_at': getattr(order, 'inventory_action_at', None) and order.inventory_action_at.strftime('%B %d, %Y at %H:%M') if hasattr(order, 'inventory_action_at') else None,
            'admin_marked_received': getattr(order, 'admin_marked_received', False),
            'admin_marked_received_at': getattr(order, 'admin_marked_received_at', None) and order.admin_marked_received_at.strftime('%B %d, %Y at %H:%M') if hasattr(order, 'admin_marked_received_at') else None
        } for order in orders]),
        
        # Team Management Data
        'inventory_users': team_data,
        'active_inventory_users': active_inventory_users,
        
        # Product Requests from Inventory
        'product_requests': product_requests,
    }
    
    # Add Billing Management Data
    from django.db.models import Sum, Count, Avg
    from datetime import date
    from collections import defaultdict
    
    # Get all bills
    all_bills = SalesBill.objects.filter(
        created_by__isnull=False
    ).select_related('created_by__userprofile').prefetch_related('items').order_by('-created_at')
    
    # Get inventory users for filter (use different variable name to avoid conflict)
    billing_inventory_users = User.objects.filter(userprofile__role='inventory')
    
    # Calculate summary statistics
    total_bills_count = all_bills.count()
    total_revenue = all_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Today's bills
    today = date.today()
    today_bills = all_bills.filter(created_at__date=today)
    today_bills_count = today_bills.count()
    
    # This month's bills
    month_bills = all_bills.filter(
        created_at__year=today.year,
        created_at__month=today.month
    )
    month_bills_count = month_bills.count()
    
    # Get available months for filter
    available_months = set()
    for bill in all_bills:
        month_str = bill.created_at.strftime('%Y-%m')
        available_months.add(month_str)
    available_months = sorted(available_months, reverse=True)
    
    # Calculate monthly summaries by store
    monthly_summaries = []
    monthly_data = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'total': 0}))
    
    for bill in all_bills:
        if bill.created_by:
            try:
                store_name = bill.created_by.userprofile.full_identity
            except:
                # If user has no profile, use username
                store_name = bill.created_by.username
            month = bill.created_at.strftime('%B %Y')
            monthly_data[store_name][month]['count'] += 1
            monthly_data[store_name][month]['total'] += float(bill.total_amount)
    
    for store_name, months in monthly_data.items():
        for month, data in months.items():
            monthly_summaries.append({
                'store_name': store_name,
                'month': month,
                'bill_count': data['count'],
                'total_amount': data['total'],
                'avg_amount': data['total'] / data['count'] if data['count'] > 0 else 0
            })
    
    # Sort by month (newest first)
    monthly_summaries.sort(key=lambda x: x['month'], reverse=True)
    
    # Add billing data to context
    context.update({
        'all_bills': all_bills,
        'billing_inventory_users': billing_inventory_users,
        'total_bills_count': total_bills_count,
        'total_revenue': total_revenue,
        'today_bills_count': today_bills_count,
        'month_bills_count': month_bills_count,
        'available_months': available_months,
        'monthly_summaries': monthly_summaries,
    })
    
    return render(request, 'admin_dashboard.html', context)

@login_required
def create_order(request):
    print(f"🔧 DEBUG: create_order view accessed")
    print(f"🔧 DEBUG: User: {request.user.username}")
    print(f"🔧 DEBUG: Method: {request.method}")
    print(f"🔧 DEBUG: POST data: {dict(request.POST)}")
    
    if request.method == 'POST':
        product_name = request.POST.get('product')
        quantity = request.POST.get('quantity')
        order_notes = request.POST.get('order_notes', '')
        
        print(f"🔧 DEBUG: Extracted data:")
        print(f"  - Product: '{product_name}'")
        print(f"  - Quantity: '{quantity}'")
        print(f"  - Notes: '{order_notes}'")
        
        if product_name and quantity:
            try:
                product = Product.objects.get(name=product_name)
                quantity = int(quantity)
                
                print(f"🔧 DEBUG: Found product: {product.name} (Stock: {product.total_stock})")
                print(f"🔧 DEBUG: Quantity to order: {quantity}")
                
                # Create the order
                order = OrderQueue.objects.create(
                    product=product,
                    quantity=quantity,
                    ordered_by=request.user,
                    order_notes=order_notes,
                    message_sent=True  # We'll send notification immediately
                )
                
                print(f"🔧 DEBUG: Order created: #{order.id}")
                
                # Create notification for inventory team
                notification = Notification.objects.create(
                    title=f"📦 NEW ORDER REQUEST: {product.name}",
                    message=f"Admin has requested to order:\n\n"
                           f"Product: {product.name}\n"
                           f"Requested Quantity: {quantity} units\n"
                           f"Current Stock: {product.total_stock} units\n"
                           f"Order Notes: {order_notes if order_notes else 'No additional notes'}\n\n"
                           f"📋 ACTION REQUIRED:\n"
                           f"1. Click 'Receive Message' to acknowledge\n"
                           f"2. Contact supplier to place order\n"
                           f"3. Update order status when placed\n"
                           f"4. Add received stock when delivered\n\n"
                           f"Order ID: #{order.id}\n"
                           f"Requested by: {request.user.first_name or request.user.username}\n"
                           f"Request Time: {timezone.now().strftime('%B %d, %Y at %H:%M')}",
                    notification_type='order_request',
                    priority='urgent',
                    target_user_role='inventory',
                    product=product
                )
                
                print(f"🔧 DEBUG: Notification created: #{notification.id}")
                print(f"  - Title: {notification.title}")
                print(f"  - Type: {notification.notification_type}")
                print(f"  - Target: {notification.target_user_role}")
                print(f"  - Priority: {notification.priority}")
                
                # Verify notification can be found by inventory query
                inventory_check = Notification.objects.filter(
                    target_user_role__in=['inventory', 'all'],
                    is_read=False,
                    notification_type='order_request'
                ).count()
                
                print(f"🔧 DEBUG: Total order_request notifications for inventory: {inventory_check}")
                
                messages.success(request, f'✅ Order request created successfully! Inventory team has been notified about {quantity} units of {product.name}. (Order ID: #{order.id}, Notification ID: #{notification.id})')
                
            except Product.DoesNotExist:
                print(f"🔧 DEBUG: Product not found: {product_name}")
                messages.error(request, f'❌ Product "{product_name}" not found!')
            except ValueError as e:
                print(f"🔧 DEBUG: Invalid quantity: {quantity} - {e}")
                messages.error(request, '❌ Invalid quantity value!')
            except Exception as e:
                print(f"🔧 DEBUG: Error creating order: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'❌ Error creating order: {str(e)}')
        else:
            print(f"🔧 DEBUG: Missing required fields - Product: {product_name}, Quantity: {quantity}")
            messages.error(request, '❌ Product name and quantity are required!')
    
    return redirect('admin_dashboard')

@login_required
def admin_mark_order_seen(request):
    """Handle admin marking order as seen - this should mark order as received"""
    print(f"🔧 DEBUG: admin_mark_order_seen view accessed")
    print(f"🔧 DEBUG: User: {request.user.username}")
    print(f"🔧 DEBUG: Method: {request.method}")
    print(f"🔧 DEBUG: POST data: {dict(request.POST)}")
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        
        print(f"🔧 DEBUG: Order ID: {order_id}")
        
        if order_id:
            try:
                order = OrderQueue.objects.get(id=order_id)
                
                print(f"🔧 DEBUG: Found order: {order.product.name} - Status: {order.status}")
                
                # Check if user is admin or the one who created the order
                if not (request.user.userprofile.role == 'admin' or order.ordered_by == request.user):
                    print(f"🔧 DEBUG: Permission denied - User role: {request.user.userprofile.role}")
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Permission denied. Only admin or order creator can mark as seen.'
                        })
                    else:
                        messages.error(request, '❌ Permission denied!')
                        return redirect('admin_dashboard')
                
                # Mark order as received by admin (final step)
                old_status = order.status
                order.status = 'received'  # Change status to received
                
                # Track admin action
                if hasattr(order, 'admin_marked_received'):
                    order.admin_marked_received = True
                    order.admin_marked_received_at = timezone.now()
                
                order.save()
                
                print(f"🔧 DEBUG: Order marked as received by admin at: {timezone.now()}")
                
                # Create notification for inventory team
                Notification.objects.create(
                    title=f"✅ ORDER COMPLETED: {order.product.name}",
                    message=f"Admin has marked the order as received and completed:\n\n"
                           f"📋 ORDER DETAILS:\n"
                           f"Product: {order.product.name}\n"
                           f"Quantity: {order.quantity} units\n"
                           f"Previous Status: {old_status.title()}\n"
                           f"New Status: Received ✅\n\n"
                           f"👤 COMPLETED BY:\n"
                           f"Admin: {request.user.first_name or request.user.username}\n"
                           f"Completion Time: {timezone.now().strftime('%B %d, %Y at %H:%M')}\n\n"
                           f"📋 WORKFLOW SUMMARY:\n"
                           f"1. ✅ Order created by admin\n"
                           f"2. ✅ Inventory acknowledged request\n"
                           f"3. ✅ Inventory placed order with supplier\n"
                           f"4. ✅ Admin marked as received\n\n"
                           f"Order ID: #{order.id}",
                    notification_type='order_completed',
                    priority='low',
                    target_user_role='inventory',
                    product=order.product
                )
                
                print(f"🔧 DEBUG: Completion notification created for inventory team")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Calculate updated counts for real-time update
                    received_count = OrderQueue.objects.filter(status='received').count()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Order marked as received successfully!',
                        'received_at': timezone.now().strftime('%B %d, %Y at %H:%M'),
                        'updated_received_count': received_count
                    })
                else:
                    messages.success(request, f'✅ Order for {order.product.name} marked as received!')
                    
            except OrderQueue.DoesNotExist:
                print(f"🔧 DEBUG: Order not found with ID: {order_id}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Order not found'
                    })
                else:
                    messages.error(request, '❌ Order not found!')
            except Exception as e:
                print(f"🔧 DEBUG: Error in admin_mark_order_seen: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'❌ Error: {str(e)}')
        else:
            print(f"🔧 DEBUG: No order ID provided")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'No order ID provided'
                })
            else:
                messages.error(request, '❌ No order ID provided!')
    
    return redirect('admin_dashboard')

@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(OrderQueue, id=order_id)
    new_status = request.POST.get('status')
    
    if new_status in ['pending', 'ordered', 'received']:
        old_status = order.status
        order.status = new_status
        order.save()
        
        messages.success(request, f'Order status updated from {old_status} to {new_status}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('admin_dashboard')

@login_required
def acknowledge_order_message(request):
    """Handle inventory team acknowledging order messages"""
    if request.method == 'POST':
        notification_id = request.POST.get('order_id')  # This is actually notification ID
        
        if notification_id:
            try:
                # Find the notification first
                notification = Notification.objects.get(
                    id=notification_id,
                    notification_type='order_request'
                )
                
                # Extract order ID from notification message (we'll need to find the order by product and recent creation)
                product = notification.product
                
                # Find the most recent pending order for this product
                order = OrderQueue.objects.filter(
                    product=product,
                    message_sent=True,
                    message_received=False
                ).order_by('-created_at').first()
                
                if not order:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Order not found or already acknowledged'
                        })
                    else:
                        messages.error(request, '❌ Order not found or already acknowledged!')
                        return redirect('inventory_dashboard')
                
                # Mark order as acknowledged by inventory
                order.message_received = True
                order.message_received_at = timezone.now()
                
                # Track inventory action
                if hasattr(order, 'inventory_action'):
                    order.inventory_action = 'acknowledged'
                    order.inventory_action_by = request.user
                    order.inventory_action_at = timezone.now()
                
                order.save()
                
                # Mark notification as read
                notification.is_read = True
                notification.save()
                
                # Create notification for admin about acknowledgment
                if order.ordered_by:
                    Notification.objects.create(
                        title=f"📨 MESSAGE ACKNOWLEDGED: {order.product.name}",
                        message=f"Inventory team has acknowledged your order request:\n\n"
                               f"📋 ORDER DETAILS:\n"
                               f"Product: {order.product.name}\n"
                               f"Quantity Requested: {order.quantity} units\n"
                               f"Current Stock: {order.product.total_stock} units\n"
                               f"Order Notes: {order.order_notes if order.order_notes else 'No additional notes'}\n\n"
                               f"👤 ACKNOWLEDGED BY:\n"
                               f"Inventory Manager: {request.user.first_name or request.user.username}\n"
                               f"Acknowledged Time: {timezone.now().strftime('%B %d, %Y at %H:%M')}\n\n"
                               f"📦 NEXT STEPS:\n"
                               f"1. Inventory will contact supplier\n"
                               f"2. Order status will be updated when placed\n"
                               f"3. Stock will be added when received\n\n"
                               f"Order ID: #{order.id}\n"
                               f"Status: Acknowledged ✅",
                        notification_type='admin_message',
                        priority='medium',
                        target_user_role='admin',
                        product=order.product
                    )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Calculate updated counts for real-time update
                    # Use admin seen count as completed count
                    updated_completed_count = OrderQueue.objects.filter(message_received=True).count()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Order message acknowledged for {order.product.name}',
                        'updated_completed_count': updated_completed_count
                    })
                else:
                    messages.success(request, f'✅ Order message acknowledged! Admin has been notified that you received the order request for {order.product.name}.')
                    
            except Notification.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Notification not found'
                    })
                else:
                    messages.error(request, '❌ Notification not found!')
            except Exception as e:
                print(f"🔧 DEBUG: Error in acknowledge_order_message: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'❌ Error: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'No notification ID provided'
                })
            else:
                messages.error(request, '❌ No notification ID provided!')
    
    return redirect('inventory_dashboard')

@login_required
def update_order_from_notification(request):
    """Handle order status update from notification"""
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        status = request.POST.get('status')
        
        if notification_id and status:
            try:
                # Find the notification
                notification = Notification.objects.get(
                    id=notification_id,
                    notification_type='order_request'
                )
                
                # Find the order by product and recent creation
                product = notification.product
                order = OrderQueue.objects.filter(
                    product=product,
                    status='pending',
                    message_received=True
                ).order_by('-created_at').first()
                
                if not order:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': False,
                            'error': 'Order not found or already updated'
                        })
                    else:
                        messages.error(request, '❌ Order not found or already updated!')
                        return redirect('inventory_dashboard')
                
                # Update order status
                old_status = order.status
                order.status = status
                
                # Track inventory action
                if status == 'ordered' and hasattr(order, 'inventory_action'):
                    order.inventory_action = 'ordered'
                    order.inventory_action_by = request.user
                    order.inventory_action_at = timezone.now()
                
                order.save()
                
                # Mark notification as read
                notification.is_read = True
                notification.save()
                
                # Notify admin when inventory places order with supplier
                if status == 'ordered' and old_status != 'ordered' and order.ordered_by:
                    Notification.objects.create(
                        title=f"🚚 ORDER PLACED WITH SUPPLIER: {order.product.name}",
                        message=f"Inventory team has placed your order with supplier:\n\n"
                               f"📋 ORDER DETAILS:\n"
                               f"Product: {order.product.name}\n"
                               f"Quantity Ordered: {order.quantity} units\n"
                               f"Current Stock: {order.product.total_stock} units\n"
                               f"Order Notes: {order.order_notes if order.order_notes else 'No additional notes'}\n\n"
                               f"👤 PROCESSED BY:\n"
                               f"Inventory Manager: {request.user.first_name or request.user.username}\n"
                               f"Processed Time: {timezone.now().strftime('%B %d, %Y at %H:%M')}\n\n"
                               f"📦 NEXT STEPS:\n"
                               f"1. Wait for supplier delivery\n"
                               f"2. Add received stock when delivered\n"
                               f"3. Mark order as received in admin panel\n\n"
                               f"Order ID: #{order.id}\n"
                               f"Status: Ordered with Supplier 🚚",
                        notification_type='admin_message',
                        priority='medium',
                        target_user_role='admin',
                        product=order.product
                    )
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': f'Order status updated to {status} for {order.product.name}'
                    })
                else:
                    messages.success(request, f'✅ Order status updated to {status.title()} for {order.product.name}!')
                    
            except Notification.DoesNotExist:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': 'Notification not found'
                    })
                else:
                    messages.error(request, '❌ Notification not found!')
            except Exception as e:
                print(f"🔧 DEBUG: Error in update_order_from_notification: {e}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
                else:
                    messages.error(request, f'❌ Error: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Missing notification ID or status'
                })
            else:
                messages.error(request, '❌ Missing notification ID or status!')
    
    return redirect('inventory_dashboard')

@login_required
def billing(request):
    # Check if user has a profile
    if not hasattr(request.user, 'userprofile'):
        messages.error(request, '❌ Your account does not have a user profile. Please contact admin or create a new account through signup.')
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    if request.method == 'POST':
        # Handle multi-product billing
        products_data = request.POST.get('products_data')
        
        if products_data:
            try:
                import json
                from decimal import Decimal
                
                products = json.loads(products_data)
                
                if not products:
                    messages.error(request, '❌ No products selected for billing')
                    return redirect('billing')
                
                # Calculate total amount
                total_amount = Decimal('0.00')
                for product_data in products:
                    total_amount += Decimal(str(product_data['total']))
                
                # Create sequential bill number using unified function
                bill_number = get_next_bill_number()
                
                # Create bill
                bill = SalesBill.objects.create(
                    bill_number=bill_number,
                    total_amount=total_amount,
                    created_by=request.user  # Track who created the bill
                )
                
                # Auto-generate QR token for user if not exists
                from .models import QRToken
                user_profile = request.user.userprofile
                qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
                
                # Process each product
                insufficient_stock_products = []
                successful_products = []
                
                for product_data in products:
                    try:
                        # Get product by name
                        product = Product.objects.get(name=product_data['name'])
                        quantity = int(product_data['quantity'])
                        unit_price = Decimal(str(product_data['unitPrice']))
                        item_total = Decimal(str(product_data['total']))
                        
                        # Check available stock
                        available_stock = product.total_stock
                        
                        if available_stock >= quantity:
                            # Create bill item
                            SalesBillItem.objects.create(
                                bill=bill,
                                product=product,
                                quantity=quantity,
                                price=unit_price,
                                total=item_total
                            )
                            
                            # AUTOMATIC INVENTORY DEDUCTION using FEFO
                            remaining_qty = quantity
                            from datetime import date
                            
                            stock_batches = product.expirystock_set.filter(
                                quantity__gt=0,
                                expiry_date__gte=date.today()
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
                            
                            successful_products.append(f"{product.name} ({quantity} units)")
                            
                            # Update stock notifications for this product
                            update_stock_notifications_for_product(product)
                            
                        else:
                            insufficient_stock_products.append(f"{product.name} (Available: {available_stock}, Requested: {quantity})")
                    
                    except Product.DoesNotExist:
                        insufficient_stock_products.append(f"{product_data['name']} (Product not found)")
                    except Exception as e:
                        insufficient_stock_products.append(f"{product_data['name']} (Error: {str(e)})")
                
                # Create notifications for successful sales
                if successful_products:
                    Notification.objects.create(
                        title=f"MULTI-PRODUCT SALE: Bill #{bill.bill_number}",
                        message=f"Multi-product bill created successfully!\n"
                               f"Products sold: {', '.join(successful_products)}\n"
                               f"Total Amount: ₹{bill.total_amount}\n"
                               f"Inventory automatically updated using FEFO method.",
                        notification_type='admin_message',
                        priority='medium',
                        target_user_role='inventory'
                    )
                
                # Show results
                if insufficient_stock_products:
                    if successful_products:
                        messages.warning(request, f'⚠️ Partial success! Bill #{bill.bill_number} created for available products. Insufficient stock for: {", ".join(insufficient_stock_products)}')
                    else:
                        # Delete the bill if no products were processed
                        bill.delete()
                        messages.error(request, f'❌ Cannot create bill! Insufficient stock for: {", ".join(insufficient_stock_products)}')
                else:
                    messages.success(request, f'✅ Multi-product bill #{bill.bill_number} created successfully! Total: ₹{bill.total_amount} | All quantities automatically deducted from inventory')
                
                return redirect('billing')
                
            except json.JSONDecodeError:
                messages.error(request, '❌ Invalid product data format')
                return redirect('billing')
            except Exception as e:
                messages.error(request, f'❌ Error creating bill: {str(e)}')
                return redirect('billing')
        
        else:
            # Handle single product billing (legacy support)
            sales_form = SalesForm(request.POST)
            if sales_form.is_valid():
                product = sales_form.cleaned_data['product']
                quantity = sales_form.cleaned_data['quantity']
                
                available_stock = product.total_stock
                
                if available_stock >= quantity:
                    from decimal import Decimal
                    
                    # Create sequential bill number using unified function
                    bill_number = get_next_bill_number()
                    
                    bill = SalesBill.objects.create(
                        bill_number=bill_number,
                        total_amount=product.new_price * Decimal(str(quantity)),
                        created_by=request.user  # Track who created the bill
                    )
                    
                    # Auto-generate QR token for user if not exists
                    from .models import QRToken
                    user_profile = request.user.userprofile
                    qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
                    
                    SalesBillItem.objects.create(
                        bill=bill,
                        product=product,
                        quantity=quantity,
                        price=product.new_price,
                        total=product.new_price * Decimal(str(quantity))
                    )
                    
                    # FEFO stock deduction
                    remaining_qty = quantity
                    from datetime import date
                    stock_batches = product.expirystock_set.filter(
                        quantity__gt=0,
                        expiry_date__gte=date.today()
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
                    
                    messages.success(request, f'✅ Single product bill #{bill.bill_number} created successfully!')
                    return redirect('billing')
                else:
                    messages.error(request, f'❌ Insufficient stock! Available: {available_stock} units')
    
    # Render the multi-product billing template
    sales_form = SalesForm()
    
    # Show only bills created by the current user
    recent_bills = SalesBill.objects.filter(
        created_by=request.user
    ).prefetch_related('items__product').order_by('-created_at')[:10]
    
    from datetime import date
    from django.db.models import Sum
    
    today = date.today()
    
    # Filter today's bills by current user
    today_bills = SalesBill.objects.filter(
        created_at__date=today,
        created_by=request.user
    )
    today_sales_count = today_bills.count()
    today_sales_amount = today_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    current_month = today.month
    current_year = today.year
    
    # Filter monthly bills by current user
    monthly_bills = SalesBill.objects.filter(
        created_at__year=current_year,
        created_at__month=current_month,
        created_by=request.user
    )
    monthly_sales_count = monthly_bills.count()
    monthly_sales_amount = monthly_bills.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get shop owners and pending orders
    from .models import ShopOwner, RestockOrder
    shop_owners = ShopOwner.objects.all()
    pending_orders = RestockOrder.objects.filter(status='pending').select_related('shop_owner')
    
    context = {
        'sales_form': sales_form,
        'recent_bills': recent_bills,
        'today_sales_count': today_sales_count,
        'today_sales_amount': today_sales_amount,
        'monthly_sales_count': monthly_sales_count,
        'monthly_sales_amount': monthly_sales_amount,
        'current_month_name': today.strftime('%B %Y'),
        'shop_owners': shop_owners,
        'pending_orders': pending_orders,
    }
    
    # Use the tabbed billing template
    return render(request, 'billing.html', context)

@login_required
def get_bill_details(request, bill_id):
    """AJAX endpoint to get bill details - only for bills created by current user"""
    try:
        # Only allow users to view their own bills
        bill = SalesBill.objects.prefetch_related('items__product').get(
            id=bill_id,
            created_by=request.user
        )
        bill_data = {
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.strftime('%b %d, %Y %H:%M'),
            'total_amount': str(bill.total_amount),
            'created_by': bill.created_by.first_name or bill.created_by.username if bill.created_by else 'Unknown',
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
        return JsonResponse({'error': 'Bill not found or access denied'}, status=404)

@login_required
def get_product_details(request, product_id):
    """AJAX endpoint to get product stock details with exact inventory quantities"""
    try:
        product = Product.objects.get(id=product_id)
        from datetime import date
        
        # Get exact inventory quantities (non-expired stock batches)
        stock_batches = product.expirystock_set.filter(
            quantity__gt=0,
            expiry_date__gte=date.today()  # Only non-expired stock
        ).order_by('expiry_date')
        
        batches_data = []
        total_available = 0
        for batch in stock_batches:
            days_to_expiry = (batch.expiry_date - date.today()).days
            batches_data.append({
                'quantity': batch.quantity,
                'expiry_date': batch.expiry_date.strftime('%b %d, %Y'),
                'days_to_expiry': days_to_expiry
            })
            total_available += batch.quantity
        
        # Check if there's expired stock
        expired_stock = product.expired_stock
        
        product_data = {
            'name': product.name,
            'category': product.category,
            'total_stock': total_available,  # Exact quantity available for billing
            'expired_stock': expired_stock,
            'current_price': str(product.new_price),
            'selling_price': str(product.selling_price),
            'cost_price': str(product.cost_price),
            'abc_classification': product.calculated_abc_classification,
            'trend_score': float(product.trend_score),
            'batches': batches_data,
            'max_sellable_quantity': total_available,  # Maximum quantity that can be sold
            'inventory_message': f"Inventory has {total_available} units available for sale"
        }
        
        return JsonResponse(product_data)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)

@login_required
def search_products_api(request):
    """API endpoint to search products with their exact inventory quantities"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'products': []})
    
    # Search products by name
    products = Product.objects.filter(
        name__icontains=query
    ).order_by('name')[:10]
    
    products_data = []
    for product in products:
        # Get exact available quantity for each product
        available_qty = product.total_stock
        
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'available_quantity': available_qty,
            'price': str(product.new_price),
            'display_text': f"{product.name} (Available: {available_qty} units)"
        })
    
    return JsonResponse({'products': products_data})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
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

def home_view(request):
    """
    Home view that handles persistent login sessions.
    If user is already logged in, redirect to their role-based dashboard.
    If not logged in, redirect to signup page (create account first).
    """
    if request.user.is_authenticated:
        try:
            profile = request.user.userprofile
            # User is already logged in, redirect to their dashboard
            if profile.role == 'inventory':
                return redirect('inventory_dashboard')
            elif profile.role == 'marketing':
                return redirect('trend_dashboard')
            elif profile.role == 'admin':
                return redirect('admin_dashboard')
            else:
                # Default fallback
                return redirect('inventory_dashboard')
        except UserProfile.DoesNotExist:
            # User has no profile, redirect to inventory dashboard as default
            return redirect('inventory_dashboard')
    else:
        # User is not logged in, redirect to signup page (create account first)
        return redirect('signup')

@login_required
def test_eye_icon(request):
    """Test page for eye icon functionality"""
    from django.http import HttpResponse
    
    with open('test_eye_icon.html', 'r') as f:
        content = f.read()
    
    return HttpResponse(content)

@login_required
def product_autocomplete_api(request):
    """API endpoint for product autocomplete with category information"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'products': []})
    
    try:
        # Search products by name (case-insensitive, partial match)
        products = Product.objects.filter(
            name__icontains=query
        ).values('id', 'name', 'category')[:10]  # Limit to 10 results
        
        product_list = []
        for product in products:
            product_list.append({
                'id': product['id'],
                'name': product['name'],
                'category': product['category']
            })
        
        return JsonResponse({'products': product_list})
        
    except Exception as e:
        print(f"🔧 DEBUG: Error in product autocomplete: {e}")
        return JsonResponse({'products': [], 'error': str(e)})
@login_required
def delete_team_member(request):
    """Handle admin deleting inventory team members - removes user from entire system"""
    print(f"🔧 DEBUG: delete_team_member called - Method: {request.method}")
    print(f"🔧 DEBUG: User: {request.user.username}")
    print(f"🔧 DEBUG: POST data: {dict(request.POST)}")
    
    if request.method == 'POST':
        # Check if user is admin
        try:
            if request.user.userprofile.role != 'admin':
                print(f"🔧 DEBUG: Permission denied - user role: {request.user.userprofile.role}")
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied. Only admin can delete team members.'
                })
        except UserProfile.DoesNotExist:
            print(f"🔧 DEBUG: User profile not found for user: {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'User profile not found.'
            })
        
        user_id = request.POST.get('user_id')
        print(f"🔧 DEBUG: Received user_id: {user_id}")
        
        if not user_id:
            print(f"🔧 DEBUG: No user_id provided")
            return JsonResponse({
                'success': False,
                'error': 'User ID not provided.'
            })
        
        try:
            # Get the user to delete
            user_to_delete = User.objects.get(id=user_id)
            print(f"🔧 DEBUG: Found user to delete: {user_to_delete.username}")
            
            # Check if user is inventory role
            try:
                profile = user_to_delete.userprofile
                print(f"🔧 DEBUG: User role: {profile.role}")
                if profile.role != 'inventory':
                    return JsonResponse({
                        'success': False,
                        'error': 'Can only delete inventory team members.'
                    })
            except UserProfile.DoesNotExist:
                print(f"🔧 DEBUG: Profile not found for user to delete")
                return JsonResponse({
                    'success': False,
                    'error': 'User profile not found.'
                })
            
            # Prevent admin from deleting themselves
            if user_to_delete.id == request.user.id:
                print(f"🔧 DEBUG: Admin trying to delete themselves")
                return JsonResponse({
                    'success': False,
                    'error': 'Cannot delete your own account.'
                })
            
            # Store username for response
            deleted_username = user_to_delete.username
            
            print(f"🔧 DEBUG: Deleting user {deleted_username} (ID: {user_id})")
            
            # Clean up related data before deleting user
            # 1. Update OrderQueue entries where this user was involved
            orders_updated = OrderQueue.objects.filter(inventory_action_by=user_to_delete).update(
                inventory_action_by=None,
                inventory_action='none'
            )
            print(f"🔧 DEBUG: Updated {orders_updated} order queue entries")
            
            # 2. The user deletion will automatically cascade delete:
            #    - UserProfile (due to CASCADE relationship)
            #    - Any other related objects with CASCADE
            
            # Delete the user (this will cascade delete UserProfile and clean up references)
            user_to_delete.delete()
            
            print(f"🔧 DEBUG: Successfully deleted user {deleted_username}")
            
            return JsonResponse({
                'success': True,
                'message': f'Team member "{deleted_username}" has been successfully deleted from the entire system.',
                'deleted_username': deleted_username
            })
            
        except User.DoesNotExist:
            print(f"🔧 DEBUG: User not found with ID: {user_id}")
            return JsonResponse({
                'success': False,
                'error': 'User not found.'
            })
        except Exception as e:
            print(f"🔧 DEBUG: Error deleting team member: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'An error occurred: {str(e)}'
            })
    
    print(f"🔧 DEBUG: Invalid request method: {request.method}")
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    })

@login_required
def get_user_profile(request):
    """Get individual user's work profile and activity"""
    if request.method == 'GET':
        # Check if user is admin
        try:
            if request.user.userprofile.role != 'admin':
                return JsonResponse({
                    'success': False,
                    'error': 'Permission denied. Only admin can view team member profiles.'
                })
        except UserProfile.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User profile not found.'
            })
        
        user_id = request.GET.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'No user ID provided'
            })
        
        try:
            # Get the user
            user = User.objects.get(id=user_id)
            
            # Security check: Only allow viewing inventory users
            try:
                profile = UserProfile.objects.get(user=user)
                if profile.role != 'inventory':
                    return JsonResponse({
                        'success': False,
                        'error': 'Can only view inventory team members'
                    })
            except UserProfile.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User profile not found'
                })
            
            # Get user's specific work data
            
            # 1. Orders acknowledged by this user
            acknowledged_orders = OrderQueue.objects.filter(
                inventory_action_by=user,
                inventory_action='acknowledged'
            ).select_related('product', 'ordered_by').order_by('-inventory_action_at')
            
            # 2. Orders placed by this user
            placed_orders = OrderQueue.objects.filter(
                inventory_action_by=user,
                inventory_action='ordered'
            ).select_related('product', 'ordered_by').order_by('-inventory_action_at')
            
            # 3. Notifications sent to inventory during this user's active period
            user_notifications = Notification.objects.filter(
                target_user_role__in=['inventory', 'all'],
                created_at__gte=user.date_joined
            ).order_by('-created_at')[:10]  # Last 10 notifications during their tenure
            
            # 4. Stock entries added during this user's active period
            recent_stock_entries = ExpiryStock.objects.filter(
                created_at__gte=user.date_joined
            ).select_related('product').order_by('-created_at')[:10]
            
            # Prepare response data
            user_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name or user.username,
                'last_name': user.last_name or '',
                'email': user.email or 'No email provided',
                'date_joined': user.date_joined.strftime('%B %d, %Y at %H:%M'),
                'role': profile.get_role_display()
            }
            
            # Acknowledged orders data
            acknowledged_data = []
            for order in acknowledged_orders:
                acknowledged_data.append({
                    'id': order.id,
                    'product_name': order.product.name,
                    'quantity': order.quantity,
                    'status': order.get_status_display(),
                    'acknowledged_at': order.inventory_action_at.strftime('%B %d, %Y at %H:%M') if order.inventory_action_at else 'N/A',
                    'ordered_by': order.ordered_by.first_name or order.ordered_by.username if order.ordered_by else 'System',
                    'notes': order.order_notes or 'No notes'
                })
            
            # Placed orders data
            placed_data = []
            for order in placed_orders:
                placed_data.append({
                    'id': order.id,
                    'product_name': order.product.name,
                    'quantity': order.quantity,
                    'status': order.get_status_display(),
                    'placed_at': order.inventory_action_at.strftime('%B %d, %Y at %H:%M') if order.inventory_action_at else 'N/A',
                    'ordered_by': order.ordered_by.first_name or order.ordered_by.username if order.ordered_by else 'System',
                    'notes': order.order_notes or 'No notes'
                })
            
            # Notifications data
            notifications_data = []
            for notification in user_notifications:
                notifications_data.append({
                    'id': notification.id,
                    'title': notification.title,
                    'type': notification.get_notification_type_display(),
                    'priority': notification.get_priority_display(),
                    'created_at': notification.created_at.strftime('%B %d, %Y at %H:%M'),
                    'product_name': notification.product.name if notification.product else 'General'
                })
            
            # Stock entries data
            stock_data = []
            for stock in recent_stock_entries:
                stock_data.append({
                    'id': stock.id,
                    'product_name': stock.product.name,
                    'quantity': stock.quantity,
                    'expiry_date': stock.expiry_date.strftime('%B %d, %Y'),
                    'added_at': stock.created_at.strftime('%B %d, %Y at %H:%M')
                })
            
            # Calculate statistics
            stats = {
                'total_acknowledged': acknowledged_orders.count(),
                'total_placed': placed_orders.count(),
                'total_notifications': user_notifications.count(),
                'total_stock_entries': recent_stock_entries.count(),
                'active_days': (timezone.now().date() - user.date_joined.date()).days
            }
            
            return JsonResponse({
                'success': True,
                'user': user_data,
                'acknowledged_orders': acknowledged_data,
                'placed_orders': placed_data,
                'notifications': notifications_data,
                'stock_entries': stock_data,
                'stats': stats
            })
            
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            })
        except Exception as e:
            print(f"🔧 DEBUG: Error fetching user profile: {e}")
            return JsonResponse({
                'success': False,
                'error': f'Error fetching user profile: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


@login_required
def get_bill_details_api(request):
    """API endpoint to get bill details for modal display in admin dashboard"""
    bill_number = request.GET.get('bill_number')
    
    if not bill_number:
        return JsonResponse({'success': False, 'error': 'Bill number is required'})
    
    try:
        bill = SalesBill.objects.get(bill_number=bill_number)
        
        # Get bill items
        items = []
        for item in bill.items.all():
            items.append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': float(item.price),
                'total': float(item.total)
            })
        
        # Get store information
        try:
            store_name = bill.created_by.userprofile.full_identity if bill.created_by else 'N/A'
            store_location = bill.created_by.userprofile.store_location if bill.created_by and bill.created_by.userprofile.store_location else 'N/A'
        except:
            # If user has no profile, use username
            store_name = bill.created_by.username if bill.created_by else 'N/A'
            store_location = 'N/A'
        
        bill_data = {
            'bill_number': bill.bill_number,
            'created_at': bill.created_at.strftime('%d %B %Y, %I:%M %p'),
            'total_amount': float(bill.total_amount),
            'store_name': store_name,
            'store_location': store_location,
            'items': items
        }
        
        return JsonResponse({'success': True, 'bill': bill_data})
        
    except SalesBill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ============================================
# OFFLINE RECOVERY FEATURE (from LedgerX)
# ============================================

def offline_ledger(request, token):
    """
    Offline Recovery View: Display transaction history using QR token
    Adapted from LedgerX for Neuro Stock Project
    """
    try:
        from .models import QRToken
        
        # Find the QR token
        qr_token = get_object_or_404(QRToken, secure_token=token, is_active=True)
        
        # Mark token as accessed
        qr_token.mark_accessed()
        
        # Get user profile and transaction history
        user_profile = qr_token.user_profile
        user = user_profile.user
        
        # Check if a specific bill is requested
        requested_bill_number = request.GET.get('bill')
        highlighted_bill = None
        
        # Get all bills created by this user
        bills = SalesBill.objects.filter(created_by=user).order_by('-created_at')[:50]
        
        # Get bill details with items
        transaction_history = []
        for bill in bills:
            items = []
            total_quantity = 0
            for item in bill.items.all():
                items.append({
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'total': item.total
                })
                total_quantity += item.quantity
            
            bill_data = {
                'bill_number': bill.bill_number,
                'created_at': bill.created_at,
                'total_amount': bill.total_amount,
                'total_quantity': total_quantity,
                'items': items,
                'is_highlighted': bill.bill_number == requested_bill_number
            }
            
            if bill.bill_number == requested_bill_number:
                highlighted_bill = bill_data
            
            transaction_history.append(bill_data)
        
        context = {
            'user_profile': user_profile,
            'user': user,
            'transaction_history': transaction_history,
            'highlighted_bill': highlighted_bill,
            'token': token,
            'last_accessed': qr_token.last_accessed,
            'is_offline_mode': True
        }
        
        return render(request, 'offline_ledger.html', context)
        
    except QRToken.DoesNotExist:
        messages.error(request, '❌ Invalid or expired QR token')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'❌ Error accessing ledger: {str(e)}')
        return redirect('login')


@login_required
def generate_qr_token(request):
    """
    Generate or retrieve QR token for the logged-in user
    """
    try:
        from .models import QRToken
        
        # Get or create QR token for user's profile
        user_profile = request.user.userprofile
        qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
        
        # Generate QR code URL
        qr_url = request.build_absolute_uri(qr_token.get_qr_url())
        
        if created:
            messages.success(request, '✅ Digital Ledger QR code generated successfully!')
        
        context = {
            'qr_token': qr_token,
            'qr_url': qr_url,
            'qr_data': qr_url  # This will be used to generate QR code
        }
        
        return render(request, 'qr_token_display.html', context)
        
    except Exception as e:
        messages.error(request, f'❌ Error generating QR token: {str(e)}')
        return redirect('inventory_dashboard')


@login_required
def get_bill_qr_data(request, bill_id):
    """
    API endpoint to get QR data for a specific bill
    Returns QR code data that includes offline ledger link
    """
    try:
        from .models import QRToken
        
        bill = get_object_or_404(SalesBill, id=bill_id, created_by=request.user)
        
        # Get or create QR token for user
        user_profile = request.user.userprofile
        qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
        
        # Generate offline ledger URL
        qr_url = request.build_absolute_uri(qr_token.get_qr_url())
        
        return JsonResponse({
            'success': True,
            'qr_data': qr_url,
            'bill_number': bill.bill_number,
            'token': str(qr_token.secure_token)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def get_bill_qr_image(request, bill_number):
    """
    Generate QR code image for a specific bill
    Returns a PNG image that can be embedded in bills
    """
    try:
        import qrcode
        from io import BytesIO
        from django.http import HttpResponse
        from .models import QRToken
        
        # Get the bill
        bill = get_object_or_404(SalesBill, bill_number=bill_number, created_by=request.user)
        
        # Get or create QR token for user
        user_profile = request.user.userprofile
        qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
        
        # Generate offline ledger URL with bill reference
        qr_url = request.build_absolute_uri(qr_token.get_qr_url())
        qr_url += f"?bill={bill.bill_number}"  # Add bill number as query parameter
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Return as HTTP response
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="bill_{bill_number}_qr.png"'
        return response
        
    except ImportError:
        # If qrcode library is not installed
        return JsonResponse({
            'success': False,
            'error': 'QR code library not installed. Run: pip install qrcode[pil]'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
def qr_test_page(request):
    """
    Test page for QR code system verification
    """
    return render(request, 'qr_test_page.html')


def individual_bill_view(request, bill_number):
    """
    Public view for individual bill details via QR code
    Shows ONLY the specific bill's information
    No login required - accessible via QR code
    """
    try:
        # Get the bill by bill number
        bill = get_object_or_404(SalesBill, bill_number=bill_number)
        
        # Get bill items with product details
        items = []
        total_quantity = 0
        for item in bill.items.all():
            items.append({
                'product_name': item.product.name,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.total
            })
            total_quantity += item.quantity
        
        # Get user/store information
        user = bill.created_by
        user_profile = user.userprofile if hasattr(user, 'userprofile') else None
        
        bill_data = {
            'bill_number': bill.bill_number,
            'created_at': bill.created_at,
            'total_amount': bill.total_amount,
            'total_quantity': total_quantity,
            'items': items,
        }
        
        context = {
            'bill': bill_data,
            'user_profile': user_profile,
            'user': user,
            'is_individual_bill': True
        }
        
        return render(request, 'individual_bill.html', context)
        
    except SalesBill.DoesNotExist:
        messages.error(request, '❌ Bill not found')
        return redirect('login')
    except Exception as e:
        messages.error(request, f'❌ Error accessing bill: {str(e)}')
        return redirect('login')


@login_required
def csv_billing(request):
    """
    Handle CSV file upload for bulk billing
    CSV format: product_name, quantity
    """
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, '❌ Please upload a CSV file')
            return redirect('billing')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, '❌ File must be a CSV file')
            return redirect('billing')
        
        try:
            import csv
            from decimal import Decimal
            from io import TextIOWrapper
            
            # Read CSV file
            file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
            csv_reader = csv.DictReader(file_data)
            
            # Validate CSV headers
            required_headers = ['product_name', 'quantity']
            if not all(header in csv_reader.fieldnames for header in required_headers):
                messages.error(request, f'❌ CSV must have columns: {", ".join(required_headers)}')
                return redirect('billing')
            
            # Parse products from CSV
            products_data = []
            errors = []
            line_number = 1
            
            for row in csv_reader:
                line_number += 1
                product_name = row.get('product_name', '').strip()
                quantity_str = row.get('quantity', '').strip()
                
                if not product_name or not quantity_str:
                    errors.append(f"Line {line_number}: Missing product name or quantity")
                    continue
                
                try:
                    quantity = int(quantity_str)
                    if quantity <= 0:
                        errors.append(f"Line {line_number}: Quantity must be positive for {product_name}")
                        continue
                except ValueError:
                    errors.append(f"Line {line_number}: Invalid quantity '{quantity_str}' for {product_name}")
                    continue
                
                # Find product
                try:
                    product = Product.objects.get(name__iexact=product_name)
                    
                    # Check stock availability
                    available_stock = product.total_stock
                    if available_stock < quantity:
                        errors.append(f"Line {line_number}: Insufficient stock for {product_name} (Available: {available_stock}, Requested: {quantity})")
                        continue
                    
                    products_data.append({
                        'name': product.name,
                        'quantity': quantity,
                        'unitPrice': float(product.new_price),
                        'total': float(product.new_price * quantity)
                    })
                    
                except Product.DoesNotExist:
                    errors.append(f"Line {line_number}: Product '{product_name}' not found")
                    continue
            
            # Show errors if any
            if errors:
                error_message = "CSV processing errors:\n" + "\n".join(errors[:10])
                if len(errors) > 10:
                    error_message += f"\n... and {len(errors) - 10} more errors"
                messages.error(request, f'❌ {error_message}')
                
                if not products_data:
                    return redirect('billing')
            
            # If we have valid products, create the bill
            if products_data:
                # Calculate total amount
                total_amount = Decimal('0.00')
                for product_data in products_data:
                    total_amount += Decimal(str(product_data['total']))
                
                # Create sequential bill number
                bill_number = get_next_bill_number()
                
                # Create bill
                bill = SalesBill.objects.create(
                    bill_number=bill_number,
                    total_amount=total_amount,
                    created_by=request.user
                )
                
                # Auto-generate QR token for user if not exists
                from .models import QRToken
                user_profile = request.user.userprofile
                qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
                
                # Process each product
                successful_products = []
                
                for product_data in products_data:
                    try:
                        product = Product.objects.get(name=product_data['name'])
                        quantity = int(product_data['quantity'])
                        unit_price = Decimal(str(product_data['unitPrice']))
                        item_total = Decimal(str(product_data['total']))
                        
                        # Create bill item
                        SalesBillItem.objects.create(
                            bill=bill,
                            product=product,
                            quantity=quantity,
                            price=unit_price,
                            total=item_total
                        )
                        
                        # AUTOMATIC INVENTORY DEDUCTION using FEFO
                        remaining_qty = quantity
                        from datetime import date
                        
                        stock_batches = product.expirystock_set.filter(
                            quantity__gt=0,
                            expiry_date__gte=date.today()
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
                        
                        successful_products.append(f"{product.name} ({quantity} units)")
                        
                        # Update stock notifications for this product
                        update_stock_notifications_for_product(product)
                        
                    except Exception as e:
                        errors.append(f"Error processing {product_data['name']}: {str(e)}")
                
                # Create notification
                if successful_products:
                    Notification.objects.create(
                        title=f"CSV BULK BILLING: Bill #{bill.bill_number}",
                        message=f"Bulk bill created from CSV upload!\n"
                               f"Products sold: {', '.join(successful_products)}\n"
                               f"Total Amount: ₹{bill.total_amount}\n"
                               f"Inventory automatically updated using FEFO method.\n"
                               f"Uploaded by: {request.user.first_name or request.user.username}",
                        notification_type='admin_message',
                        priority='medium',
                        target_user_role='inventory'
                    )
                
                success_msg = (f'✅ CSV bill #{bill.bill_number} created successfully! '
                              f'Total: ₹{bill.total_amount} | {len(successful_products)} products processed')
                messages.success(request, success_msg)
                
                if errors:
                    error_summary = f'⚠️ {len(errors)} item(s) had errors and were skipped:'
                    error_details = '<br>'.join(errors[:5])  # Show first 5 errors
                    if len(errors) > 5:
                        error_details += f'<br>... and {len(errors) - 5} more errors'
                    messages.warning(request, f'{error_summary}<br>{error_details}')
            else:
                messages.error(request, '❌ No valid products found in CSV file')
            
            return redirect('billing')
            
        except Exception as e:
            messages.error(request, f'❌ Error processing CSV file: {str(e)}')
            return redirect('billing')
    
    return redirect('billing')


@login_required
def manage_shop_owners(request):
    """
    Manage shop owners and their restock orders
    """
    from .models import ShopOwner, RestockOrder
    from .forms import ShopOwnerForm, RestockOrderForm
    
    if request.method == 'POST':
        if 'add_shop_owner' in request.POST:
            form = ShopOwnerForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Shop owner added successfully!')
                return redirect('manage_shop_owners')
        
        elif 'upload_restock_order' in request.POST:
            form = RestockOrderForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, '✅ Restock order uploaded successfully!')
                return redirect('manage_shop_owners')
    
    shop_owners = ShopOwner.objects.all()
    pending_orders = RestockOrder.objects.filter(status='pending').select_related('shop_owner')
    
    context = {
        'shop_owners': shop_owners,
        'pending_orders': pending_orders,
        'shop_owner_form': ShopOwnerForm(),
        'restock_order_form': RestockOrderForm(),
    }
    
    return render(request, 'manage_shop_owners.html', context)


@login_required
def get_shop_owner_orders(request):
    """
    API endpoint to get pending orders for a shop owner
    """
    from .models import RestockOrder
    
    shop_owner_id = request.GET.get('shop_owner_id')
    
    if not shop_owner_id:
        return JsonResponse({'success': False, 'error': 'Shop owner ID required'})
    
    try:
        orders = RestockOrder.objects.filter(
            shop_owner_id=shop_owner_id,
            status='pending'
        ).values('id', 'uploaded_at', 'notes')
        
        orders_list = list(orders)
        
        return JsonResponse({
            'success': True,
            'orders': orders_list
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def process_shop_owner_order(request):
    """
    Process a shop owner's restock order and create bill
    """
    if request.method != 'POST':
        return redirect('billing')
    
    from .models import RestockOrder, ShopOwner
    import csv
    from decimal import Decimal
    
    order_id = request.POST.get('order_id')
    
    if not order_id:
        messages.error(request, '❌ Order ID required')
        return redirect('billing')
    
    try:
        order = RestockOrder.objects.get(id=order_id, status='pending')
        shop_owner = order.shop_owner
        
        # Read CSV file - open in binary mode then decode
        csv_file = order.csv_file
        csv_file.open('rb')  # Open in binary mode
        
        # Read and decode the content
        content = csv_file.read().decode('utf-8-sig')  # utf-8-sig handles BOM
        csv_file.close()
        
        # Parse CSV
        from io import StringIO
        csv_reader = csv.DictReader(StringIO(content))
        
        # Get actual fieldnames and clean them
        fieldnames = [field.strip().lower() for field in csv_reader.fieldnames] if csv_reader.fieldnames else []
        
        # Validate CSV headers (case-insensitive)
        required_headers = ['product_name', 'quantity']
        if not all(header in fieldnames for header in required_headers):
            messages.error(request, 
                f'❌ CSV must have columns: {", ".join(required_headers)}. '
                f'Found columns: {", ".join(csv_reader.fieldnames if csv_reader.fieldnames else ["none"])}')
            return redirect('billing')
        
        # Parse products from CSV
        products_data = []
        errors = []
        line_number = 1
        
        for row in csv_reader:
            line_number += 1
            # Handle case-insensitive column names
            row_lower = {k.strip().lower(): v for k, v in row.items()}
            product_name = row_lower.get('product_name', '').strip()
            quantity_str = row_lower.get('quantity', '').strip()
            
            if not product_name or not quantity_str:
                errors.append(f"Line {line_number}: Missing product name or quantity")
                continue
            
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    errors.append(f"Line {line_number}: Quantity must be positive for {product_name}")
                    continue
            except ValueError:
                errors.append(f"Line {line_number}: Invalid quantity '{quantity_str}' for {product_name}")
                continue
            
            # Find product
            try:
                product = Product.objects.get(name__iexact=product_name)
                
                # Check stock availability
                available_stock = product.total_stock
                if available_stock < quantity:
                    errors.append(f"Line {line_number}: Insufficient stock for {product_name} (Available: {available_stock}, Requested: {quantity})")
                    continue
                
                products_data.append({
                    'name': product.name,
                    'quantity': quantity,
                    'unitPrice': float(product.new_price),
                    'total': float(product.new_price * quantity)
                })
                
            except Product.DoesNotExist:
                errors.append(f"Line {line_number}: Product '{product_name}' not found")
                continue
        
        # Show errors if any
        if errors and not products_data:
            error_message = "CSV processing errors:\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                error_message += f"\n... and {len(errors) - 10} more errors"
            messages.error(request, f'❌ {error_message}')
            return redirect('billing')
        
        # If we have valid products, create the bill
        if products_data:
            # Calculate total amount
            total_amount = Decimal('0.00')
            for product_data in products_data:
                total_amount += Decimal(str(product_data['total']))
            
            # Create sequential bill number
            bill_number = get_next_bill_number()
            
            # Create bill
            bill = SalesBill.objects.create(
                bill_number=bill_number,
                total_amount=total_amount,
                created_by=request.user
            )
            
            # Auto-generate QR token for user if not exists
            from .models import QRToken
            user_profile = request.user.userprofile
            qr_token, created = QRToken.objects.get_or_create(user_profile=user_profile)
            
            # Process each product
            successful_products = []
            
            for product_data in products_data:
                try:
                    product = Product.objects.get(name=product_data['name'])
                    quantity = int(product_data['quantity'])
                    unit_price = Decimal(str(product_data['unitPrice']))
                    item_total = Decimal(str(product_data['total']))
                    
                    # Create bill item
                    SalesBillItem.objects.create(
                        bill=bill,
                        product=product,
                        quantity=quantity,
                        price=unit_price,
                        total=item_total
                    )
                    
                    # AUTOMATIC INVENTORY DEDUCTION using FEFO
                    remaining_qty = quantity
                    from datetime import date
                    
                    stock_batches = product.expirystock_set.filter(
                        quantity__gt=0,
                        expiry_date__gte=date.today()
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
                    
                    successful_products.append(f"{product.name} ({quantity} units)")
                    
                    # Update stock notifications for this product
                    update_stock_notifications_for_product(product)
                    
                except Exception as e:
                    errors.append(f"Error processing {product_data['name']}: {str(e)}")
            
            # Mark order as processed
            order.mark_processed(bill, request.user)
            
            # Create notification
            if successful_products:
                Notification.objects.create(
                    title=f"SHOP OWNER ORDER: {shop_owner.name} - Bill #{bill.bill_number}",
                    message=f"Restock order processed for {shop_owner.shop_name}!\n"
                           f"Shop Owner: {shop_owner.name}\n"
                           f"Products: {', '.join(successful_products)}\n"
                           f"Total Amount: ₹{bill.total_amount}\n"
                           f"Inventory automatically updated using FEFO method.\n"
                           f"Processed by: {request.user.first_name or request.user.username}",
                    notification_type='admin_message',
                    priority='medium',
                    target_user_role='inventory'
                )
            
            # Show detailed success message
            success_msg = (f'✅ Order from {shop_owner.name} processed! Bill #{bill.bill_number} created. '
                          f'Total: ₹{bill.total_amount} | {len(successful_products)} products processed successfully')
            messages.success(request, success_msg)
            
            # Show detailed errors if any
            if errors:
                error_summary = f'⚠️ {len(errors)} item(s) had errors and were skipped:'
                error_details = '<br>'.join(errors[:5])  # Show first 5 errors
                if len(errors) > 5:
                    error_details += f'<br>... and {len(errors) - 5} more errors'
                messages.warning(request, f'{error_summary}<br>{error_details}')
        else:
            messages.error(request, '❌ No valid products found in CSV file')
        
        return redirect('billing')
        
    except RestockOrder.DoesNotExist:
        messages.error(request, '❌ Order not found or already processed')
        return redirect('billing')
    except Exception as e:
        messages.error(request, f'❌ Error processing order: {str(e)}')
        return redirect('billing')


@login_required
def debug_csv_file(request, order_id):
    """
    Debug view to see CSV file content
    """
    from .models import RestockOrder
    
    try:
        order = RestockOrder.objects.get(id=order_id)
        
        # Read CSV file
        csv_file = order.csv_file
        csv_file.open('rb')
        content = csv_file.read().decode('utf-8-sig')
        csv_file.close()
        
        # Show raw content
        return JsonResponse({
            'success': True,
            'filename': csv_file.name,
            'content': content,
            'lines': content.split('\n')[:10]  # First 10 lines
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def load_shop_owner_csv(request):
    """
    Load products from shop owner's CSV file without creating bill
    Returns product data as JSON to populate the selected products table
    """
    from .models import RestockOrder
    import csv
    from io import StringIO
    
    order_id = request.GET.get('order_id')
    
    if not order_id:
        return JsonResponse({'success': False, 'error': 'Order ID required'})
    
    try:
        order = RestockOrder.objects.get(id=order_id, status='pending')
        shop_owner = order.shop_owner
        
        # Read CSV file
        csv_file = order.csv_file
        csv_file.open('rb')
        content = csv_file.read().decode('utf-8-sig')
        csv_file.close()
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(content))
        
        # Get actual fieldnames and clean them
        fieldnames = [field.strip().lower() for field in csv_reader.fieldnames] if csv_reader.fieldnames else []
        
        # Validate CSV headers
        required_headers = ['product_name', 'quantity']
        if not all(header in fieldnames for header in required_headers):
            return JsonResponse({
                'success': False,
                'error': f'CSV must have columns: {", ".join(required_headers)}. Found: {", ".join(csv_reader.fieldnames or ["none"])}'
            })
        
        # Parse products
        products_data = []
        errors = []
        line_number = 1
        
        for row in csv_reader:
            line_number += 1
            row_lower = {k.strip().lower(): v for k, v in row.items()}
            product_name = row_lower.get('product_name', '').strip()
            quantity_str = row_lower.get('quantity', '').strip()
            
            if not product_name or not quantity_str:
                errors.append(f"Line {line_number}: Missing product name or quantity")
                continue
            
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    errors.append(f"Line {line_number}: Quantity must be positive for {product_name}")
                    continue
            except ValueError:
                errors.append(f"Line {line_number}: Invalid quantity '{quantity_str}' for {product_name}")
                continue
            
            # Find product
            try:
                product = Product.objects.get(name__iexact=product_name)
                available_stock = product.total_stock
                
                if available_stock < quantity:
                    errors.append(f"Line {line_number}: Insufficient stock for {product_name} (Available: {available_stock}, Requested: {quantity})")
                    # Still add to list but mark as error
                    products_data.append({
                        'id': product.id,
                        'name': product.name,
                        'quantity': quantity,
                        'unitPrice': float(product.new_price),
                        'total': float(product.new_price * quantity),
                        'error': f'Insufficient stock (Available: {available_stock})',
                        'hasError': True
                    })
                else:
                    products_data.append({
                        'id': product.id,
                        'name': product.name,
                        'quantity': quantity,
                        'unitPrice': float(product.new_price),
                        'total': float(product.new_price * quantity),
                        'hasError': False
                    })
                
            except Product.DoesNotExist:
                errors.append(f"Line {line_number}: Product '{product_name}' not found")
                # Add as error item
                products_data.append({
                    'id': None,
                    'name': product_name,
                    'quantity': quantity,
                    'unitPrice': 0,
                    'total': 0,
                    'error': 'Product not found',
                    'hasError': True
                })
        
        return JsonResponse({
            'success': True,
            'products': products_data,
            'errors': errors,
            'shop_owner': {
                'name': shop_owner.name,
                'shop_name': shop_owner.shop_name
            },
            'order_id': order.id
        })
        
    except RestockOrder.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
