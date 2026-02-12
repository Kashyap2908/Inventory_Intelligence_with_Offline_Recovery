# Shop Owner CSV Billing System - User Guide

## Overview
The system allows inventory managers to process restock orders from shop owners by selecting their name and automatically loading products from their pre-uploaded CSV files.

## Workflow

### Step 1: Shop Owner Uploads CSV
Shop owners upload their restock orders through the "Manage Shop Owners" page:
1. Go to http://127.0.0.1:8000/manage-shop-owners/
2. Select shop owner from dropdown
3. Upload their CSV file
4. Order status: **Pending**

### Step 2: Inventory Manager Processes Order
1. Go to **Billing** page
2. Find "Process Shop Owner Restock Order" section
3. Select shop owner from dropdown (shows pending orders only)
4. Click **"Load Products from CSV"**
5. Products appear in "Selected Products" table
6. Review products, quantities, and prices
7. Click **"Create Bill"**
8. Bill is created and inventory is automatically deducted

## Features

### Automatic Validation
- ✅ Product name matching (case-insensitive)
- ✅ Stock availability checking
- ✅ Quantity validation
- ✅ Price calculation

### Error Handling
- Products not found are skipped with error message
- Insufficient stock items are flagged
- Invalid quantities are rejected
- Valid products are still processed

### Two-Step Process
1. **Load & Review**: Products load into table for review
2. **Create Bill**: After review, create bill with one click

## CSV Format

```csv
product_name,quantity
Rice,50
Sugar,30
Wheat Flour,40
```

### Requirements
- Column headers: `product_name`, `quantity`
- Product names must match inventory (case-insensitive)
- Quantities must be positive integers
- UTF-8 encoding recommended

## Sample Files

Located in `sample_orders/` folder:
- `rajesh_kumar_order.csv`
- `priya_sharma_order.csv`

## Adding Shop Owners

Run the script to add sample shop owners:
```bash
python add_sample_shop_owners.py
```

Or add manually through:
- Admin panel: http://127.0.0.1:8000/admin/
- Manage page: http://127.0.0.1:8000/manage-shop-owners/

## Benefits

1. **Speed**: Process bulk orders in seconds
2. **Accuracy**: Automatic validation and error checking
3. **Review**: See all products before creating bill
4. **Tracking**: All orders tracked with shop owner info
5. **Automation**: FEFO inventory deduction
6. **Transparency**: Detailed error messages

## Troubleshooting

### "No pending orders"
- Shop owner hasn't uploaded CSV file yet
- Order was already processed
- Go to "Manage Shop Owners" to upload

### "Product not found"
- Product name in CSV doesn't match inventory
- Check spelling and capitalization
- Add product to inventory first

### "Insufficient stock"
- Not enough inventory available
- Add stock before processing order
- Or reduce quantity in CSV

### Products don't load
- Check browser console for errors
- Verify CSV file format
- Ensure server is running

## Technical Details

- **File Storage**: `media/restock_orders/`
- **Status Flow**: Pending → Processed
- **Bill Format**: BILL-XXXXXX
- **Inventory Method**: FEFO (First Expired, First Out)
- **Notifications**: Auto-generated for processed orders

## Support

For issues:
1. Check CSV format matches template
2. Verify products exist in inventory
3. Check stock availability
4. Review error messages in browser console
