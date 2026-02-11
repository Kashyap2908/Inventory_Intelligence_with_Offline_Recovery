from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),  # New home view with persistent login
    path('signup/', views.user_signup, name='signup'),
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),  # Redirect to home after logout
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('trends/', views.trend_dashboard, name='trend_dashboard'),
    path('trend-dashboard/', views.trend_dashboard, name='trend_dashboard_ajax'),  # Alternative URL for AJAX
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('billing/', views.billing, name='billing'),
    path('bill-details/<int:bill_id>/', views.get_bill_details, name='get_bill_details'),
    path('get-bill-details/', views.get_bill_details_api, name='get_bill_details_api'),  # API for admin dashboard modal
    path('product-details/<int:product_id>/', views.get_product_details, name='get_product_details'),
    path('create-order/', views.create_order, name='create_order'),
    path('admin-mark-order-seen/', views.admin_mark_order_seen, name='admin_mark_order_seen'),
    path('update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('acknowledge-order/', views.acknowledge_order_message, name='acknowledge_order_message'),
    path('update-order-from-notification/', views.update_order_from_notification, name='update_order_from_notification'),
    path('api/search-products/', views.search_products, name='search_products'),
    path('api/search-products-billing/', views.search_products_api, name='search_products_api'),  # New API for billing
    path('api/product-autocomplete/', views.product_autocomplete_api, name='product_autocomplete_api'),  # New API for notification autocomplete
    path('apply-recommendation/', views.apply_recommendation, name='apply_recommendation'),
    path('dismiss-recommendation/', views.dismiss_recommendation, name='dismiss_recommendation'),
    path('delete-team-member/', views.delete_team_member, name='delete_team_member'),
    path('get-user-profile/', views.get_user_profile, name='get_user_profile'),
    path('test-eye-icon/', views.test_eye_icon, name='test_eye_icon'),  # Test page for eye icon
]