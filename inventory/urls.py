from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('trends/', views.trend_dashboard, name='trend_dashboard'),
    path('trend-dashboard/', views.trend_dashboard, name='trend_dashboard_ajax'),  # Alternative URL for AJAX
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('billing/', views.billing, name='billing'),
    path('bill-details/<int:bill_id>/', views.get_bill_details, name='get_bill_details'),
    path('product-details/<int:product_id>/', views.get_product_details, name='get_product_details'),
    path('create-order/', views.create_order, name='create_order'),
    path('update-order/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('api/search-products/', views.search_products, name='search_products'),
    path('api/search-products-billing/', views.search_products_api, name='search_products_api'),  # New API for billing
    path('apply-recommendation/', views.apply_recommendation, name='apply_recommendation'),
    path('dismiss-recommendation/', views.dismiss_recommendation, name='dismiss_recommendation'),
    path('test-eye-icon/', views.test_eye_icon, name='test_eye_icon'),  # Test page for eye icon
]