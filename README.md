# Smart Inventory Management System

A Django-based inventory management system with role-based authentication, product management, stock control, and notification system.

## Features

- **Role-based Authentication**: Inventory Manager, Marketing Manager, Admin
- **Product Management**: Add, view, and manage products with ABC classification
- **Stock Control**: FEFO (First Expired, First Out) inventory management
- **Billing System**: Create sales with real-time product details
- **Notification System**: Admin-to-inventory notifications with read tracking
- **Trend Analysis**: AI-powered trend scoring for products
- **Autocomplete**: Smart product search in forms
- **Responsive Design**: Bootstrap-based UI

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

4. **Start Server**
   ```bash
   python manage.py runserver
   ```

5. **Access System**
   - Open http://127.0.0.1:8000/
   - Login or create account
   - Access different dashboards based on role

## User Roles

- **Inventory Manager**: Manage products, stock, view notifications
- **Marketing Manager**: View trends and analytics
- **Admin**: Send notifications, apply discounts, manage orders

## Core Files

- `manage.py` - Django management script
- `inventory/models.py` - Database models
- `inventory/views.py` - Business logic
- `inventory/forms.py` - Form definitions
- `inventory/urls.py` - URL routing
- `templates/` - HTML templates
- `static/css/` - Styling files
- `db.sqlite3` - SQLite database

## Database Models

- **Product**: Product information with pricing and classification
- **ExpiryStock**: Stock batches with expiry dates
- **Notification**: Admin-to-inventory messaging system
- **SalesBill**: Sales transactions
- **OrderQueue**: Purchase orders
- **UserProfile**: User role management

## Key Features

### Notification System
- Admin can send notifications to inventory team
- Real-time read/unread status tracking
- Product-specific notifications with details
- History tracking for audit purposes

### Product Autocomplete
- Type-ahead search in product fields
- Shows product details (stock, price, category)
- Keyboard navigation support
- Works across all forms

### FEFO Stock Management
- Automatic stock deduction from earliest expiry dates
- Prevents expired product sales
- Stock level monitoring and alerts

### Responsive Design
- Mobile-friendly interface
- Professional Bootstrap styling
- Intuitive user experience

## Technology Stack

- **Backend**: Django 4.2.7, Python 3.13
- **Database**: SQLite3
- **Frontend**: Bootstrap 5.1.3, JavaScript
- **Icons**: Font Awesome 6.0
- **Styling**: Custom CSS with Bootstrap

## Project Structure

```
smart_inventory/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── inventory/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── inventory_dashboard.html
│   ├── admin_dashboard.html
│   ├── billing.html
│   └── trend_dashboard.html
└── static/
    └── css/
        ├── professional.css
        └── style.css
```

## License

This project is for educational purposes.