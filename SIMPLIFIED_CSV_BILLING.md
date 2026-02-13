# Simplified CSV Billing System

## Overview
The new simplified CSV billing system allows you to process shop owner restock orders with a **single CSV file** that contains both shop owner information and product details.

## CSV Format

### Structure
```csv
Shop Owner Name,Shop Name,Email
[Owner Name],[Shop Name],[Email Address]

product_name,quantity
[Product 1],[Quantity 1]
[Product 2],[Quantity 2]
...
```

### Example
```csv
Shop Owner Name,Shop Name,Email
Rajesh Kumar,Kumar General Store,rajesh@kumarstore.com

product_name,quantity
Rice,50
Sugar,30
Wheat Flour,40
Cooking Oil,25
```

## How It Works

1. **Upload CSV**: Go to Billing Dashboard → "Process Shop Owner Restock Order (CSV)" section
2. **Select File**: Click "Choose File" and select your complete CSV file
3. **Submit**: Click "Upload & Create Bill"
4. **Automatic Processing**:
   - System reads shop owner details (name, shop, email)
   - Validates all products and quantities
   - Checks stock availability
   - Creates bill with verification code
   - Deducts inventory using FEFO (First Expired, First Out)
   - **Automatically sends email** to shop owner with bill details and verification code

## Features

✅ **Single CSV Upload** - No need to add shop owner separately
✅ **Automatic Email** - Bill sent immediately with verification code
✅ **FEFO Inventory Deduction** - Oldest stock used first
✅ **Error Handling** - Shows which products had issues
✅ **Validation** - Checks stock availability before creating bill
✅ **Verification Code** - Unique 8-character code for each bill

## Email Content

Shop owners receive an email with:
- Bill number
- Verification code (8-character unique code)
- Date and time
- Complete product list with quantities and prices
- Total amount

## Sample CSV Download

Download the sample CSV file from the billing page to see the correct format.

## Important Notes

- **Email is required** in the CSV file
- **Product names must match exactly** with products in inventory
- **Quantities must be positive integers**
- **Stock availability is checked** before bill creation
- **Empty lines are skipped** automatically
- **First 3 lines** are for shop owner info (header, data, blank line)
- **Line 4 onwards** are for products (header + data rows)

## Error Messages

- ❌ "CSV file is too short" - Need at least 4 lines (owner info + product header)
- ❌ "Shop owner info incomplete" - Missing name, shop name, or email
- ❌ "Invalid email address" - Email format is incorrect
- ❌ "Product not found" - Product name doesn't match inventory
- ❌ "Insufficient stock" - Not enough stock available
- ⚠️ "Some items had errors" - Bill created but some products skipped

## Success Flow

1. CSV uploaded ✓
2. Shop owner validated ✓
3. Products validated ✓
4. Stock checked ✓
5. Bill created ✓
6. Inventory deducted (FEFO) ✓
7. Email sent ✓
8. Notification created ✓

## Comparison: Old vs New

### Old System (2 Steps)
1. Add shop owner to database
2. Upload separate CSV with products
3. Select shop owner from dropdown
4. Load CSV
5. Create bill
6. Manual email sending

### New System (1 Step)
1. Upload complete CSV with owner + products
2. ✅ Done! (Bill created + Email sent automatically)

## Technical Details

- **Endpoint**: `/process-complete-csv-order/`
- **Method**: POST
- **File Parameter**: `complete_csv_file`
- **Encoding**: UTF-8 with BOM support
- **Email Backend**: Gmail SMTP
- **Verification Code**: 8-character alphanumeric (uppercase)
