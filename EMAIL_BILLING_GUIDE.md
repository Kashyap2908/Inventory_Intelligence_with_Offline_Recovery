# Email Billing System with Verification Codes

## Overview
When a bill is created for a shop owner, the system automatically:
1. Generates a unique 8-character verification code
2. Sends an email to the shop owner with bill details
3. Displays the verification code to the inventory manager

## Features

### Unique Verification Code
- **Format**: 8 characters (uppercase letters + digits)
- **Example**: `A7K9M2X4`
- **Uniqueness**: Guaranteed unique across all bills
- **Purpose**: Shop owner can verify bill authenticity

### Email Content
The email includes:
- Bill number
- Verification code
- Date and time
- Complete product list with quantities and prices
- Total amount
- Professional formatting

### Email Tracking
- `email_sent`: Boolean flag
- `email_sent_at`: Timestamp
- Visible in admin panel and notifications

## Configuration

### Development (Current)
Emails print to console where Django server runs:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Production (Gmail Example)
Update `smart_inventory/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'  # Use App Password, not regular password
DEFAULT_FROM_EMAIL = 'NeuroStock <your-email@gmail.com>'
```

### Gmail App Password Setup
1. Go to Google Account settings
2. Security → 2-Step Verification (enable if not enabled)
3. App passwords → Generate new app password
4. Use generated password in settings

## Usage

### For Inventory Manager
1. Process shop owner order as usual
2. After bill creation, you'll see:
   - ✅ Success message with bill number
   - 📧 Email status message
   - 📋 Verification code displayed

### For Shop Owner
1. Receives email with:
   - Bill details
   - Verification code
   - Product breakdown
2. Can verify bill authenticity using code
3. Keeps code for records

## Email Sample

```
Subject: Bill #BILL-000001 - NeuroStock Inventory

Dear Rajesh Kumar,

Your restock order has been processed successfully!

Bill Details:
-------------
Bill Number: BILL-000001
Verification Code: A7K9M2X4
Date: February 12, 2026 at 20:30
Total Amount: ₹5,250.00

Products:
---------
• Rice: 50 units @ ₹50.00 = ₹2,500.00
• Sugar: 30 units @ ₹45.00 = ₹1,350.00
• Wheat Flour: 40 units @ ₹35.00 = ₹1,400.00

---------
Grand Total: ₹5,250.00

IMPORTANT: Your Verification Code is A7K9M2X4
Please keep this code safe for your records.

Thank you for your business!

Best regards,
NeuroStock Inventory Management
```

## Database Fields

### SalesBill Model
- `verification_code`: CharField(8) - Unique code
- `email_sent`: Boolean - Email status
- `email_sent_at`: DateTime - When email was sent

## Error Handling

### No Email Address
- Verification code still generated
- Message: "Verification code: XXXXXXXX (No email address for shop owner)"
- Code displayed to inventory manager

### Email Failure
- Bill still created successfully
- Warning message shown
- Verification code available
- Can resend manually if needed

## Benefits

1. **Security**: Unique codes prevent fraud
2. **Verification**: Shop owners can confirm bill authenticity
3. **Record Keeping**: Both parties have verification code
4. **Professional**: Automated email communication
5. **Tracking**: Know which bills were emailed
6. **Audit Trail**: Email timestamps recorded

## Testing

### View Email in Console
1. Start Django server: `python manage.py runserver`
2. Process a shop owner order
3. Check console output for email content
4. Verification code will be displayed

### Check Database
```python
from inventory.models import SalesBill

# Get bill
bill = SalesBill.objects.get(bill_number='BILL-000001')

# Check verification code
print(bill.verification_code)  # e.g., 'A7K9M2X4'

# Check email status
print(bill.email_sent)  # True/False
print(bill.email_sent_at)  # Timestamp or None
```

## Future Enhancements

Possible additions:
- SMS notification with verification code
- QR code with verification code
- Email templates with HTML formatting
- Resend email functionality
- Verification code lookup page
- PDF attachment with bill details

## Troubleshooting

### Email not sending
- Check EMAIL_BACKEND in settings.py
- Verify SMTP credentials (production)
- Check shop owner has email address
- Review console/logs for errors

### Verification code not generated
- Check database migration ran successfully
- Verify SalesBill model has verification_code field
- Check for unique constraint errors

### Email goes to spam
- Use proper FROM email address
- Configure SPF/DKIM records (production)
- Use professional email content
- Avoid spam trigger words
