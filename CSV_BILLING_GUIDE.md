# CSV Bulk Billing Guide

## Overview
The CSV Bulk Billing feature allows inventory managers to quickly create bills by uploading a CSV file containing product restock orders from shop owners.

## How It Works

1. **Shop Owner Sends CSV**: Shop owners create a CSV file with products they want to restock
2. **Upload to System**: Inventory manager uploads the CSV file through the billing page
3. **Automatic Processing**: System validates products, checks stock availability, and creates a bill
4. **Inventory Deduction**: Stock is automatically deducted using FEFO (First Expired, First Out) method

## CSV File Format

### Required Columns
- `product_name`: Exact name of the product (case-insensitive)
- `quantity`: Number of units to order (must be positive integer)

### Example CSV File
```csv
product_name,quantity
Rice,50
Sugar,30
Wheat Flour,40
Cooking Oil,25
Salt,20
```

### CSV Rules
1. First row must be headers: `product_name,quantity`
2. Product names must match exactly with products in your inventory
3. Quantities must be positive integers
4. Empty rows are ignored
5. Products with insufficient stock will be skipped with error messages

## Using the Feature

### Step 1: Prepare CSV File
- Ask shop owner to provide restock list in CSV format
- Use `sample_restock_order.csv` as a template
- Ensure product names match your inventory

### Step 2: Upload CSV
1. Go to Billing page
2. Find "CSV Bulk Billing" section at the top
3. Click "Choose File" and select the CSV
4. Click "Upload & Create Bill"

### Step 3: Review Results
- System shows success message with bill number and total amount
- If any products have errors, they are listed separately
- Valid products are processed even if some have errors

## Error Handling

### Common Errors
- **Product not found**: Product name doesn't match inventory
- **Insufficient stock**: Not enough stock available
- **Invalid quantity**: Quantity is not a positive number
- **Missing data**: Product name or quantity is empty

### What Happens on Errors
- Valid products are still processed
- Bill is created for available products
- Error messages show which products failed and why
- No partial deductions - each product is fully processed or skipped

## Benefits

1. **Speed**: Process multiple products in seconds
2. **Accuracy**: Reduces manual entry errors
3. **Automation**: Automatic inventory deduction using FEFO
4. **Tracking**: All bills are tracked with unique bill numbers
5. **Notifications**: System creates notifications for inventory updates

## Sample CSV File

A sample CSV file (`sample_restock_order.csv`) is included in the project root. Use it as a template for shop owners.

## Tips

1. **Standardize Product Names**: Ensure shop owners use exact product names
2. **Regular Updates**: Keep product list updated and share with shop owners
3. **Batch Processing**: Combine multiple small orders into one CSV for efficiency
4. **Stock Checks**: Verify stock levels before processing large orders
5. **Error Review**: Always review error messages to fix data issues

## Technical Details

- **File Type**: Only `.csv` files accepted
- **Encoding**: UTF-8 encoding recommended
- **Size Limit**: No specific limit, but keep files reasonable (< 1000 products)
- **Processing**: Sequential processing with FEFO inventory deduction
- **Bill Generation**: Automatic bill number generation (BILL-XXXXXX format)

## Support

For issues or questions:
1. Check product names match exactly
2. Verify CSV format matches the template
3. Ensure sufficient stock is available
4. Review error messages for specific issues
