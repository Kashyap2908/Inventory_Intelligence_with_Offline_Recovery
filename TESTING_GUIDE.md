# Bill Printing - Testing Guide

## Quick Test Instructions

### Test 1: Admin Dashboard Bill Printing

1. **Login as Admin**
   - Username: `admin`
   - Password: `admin123`

2. **Navigate to Admin Dashboard**
   - Click "Admin" in navigation bar
   - Go to "Billing Management" tab (7th tab)

3. **View a Bill**
   - Find any bill in the "Daily Bills" table
   - Click the "View" button (eye icon)
   - ✅ Modal should open immediately with bill details
   - ✅ No blur on background
   - ✅ All details visible (bill number, date, store, items, total)

4. **Print the Bill**
   - Click "Print Bill" button in modal
   - ✅ New window opens with white background
   - ✅ Professional header: "NeuroStock Inventory Management"
   - ✅ All bill details visible
   - ✅ Items table with borders
   - ✅ Grand total displayed
   - ✅ Print preview shows white background

5. **Verify Print Output**
   - Press Ctrl+P or click print
   - ✅ Print preview shows clean, professional bill
   - ✅ White background (not gray or colored)
   - ✅ All text is readable
   - ✅ Tables have proper borders

---

### Test 2: Billing Page Bill Printing

1. **Login as Inventory User**
   - Username: `mumbai_store` (or any inventory user)
   - Password: `mumbai123`

2. **Navigate to Billing Page**
   - Click "Billing" in navigation bar
   - Go to "Recent Bills" tab

3. **View a Bill**
   - Find any bill in the recent bills table
   - Click the "View" button
   - ✅ Loading spinner appears briefly (no blur)
   - ✅ Modal opens with bill details
   - ✅ All items displayed correctly
   - ✅ Total amount visible

4. **Print the Bill**
   - Click "Print Bill" button in modal
   - ✅ New window opens with white background
   - ✅ Professional header with company name
   - ✅ Bill information section
   - ✅ Items table with all products
   - ✅ Footer with thank you message
   - ✅ Generation timestamp

5. **Verify Print Output**
   - Press Ctrl+P or click print
   - ✅ Print preview shows clean bill
   - ✅ White background
   - ✅ All details included
   - ✅ Professional appearance

---

## Expected Results

### ✅ What Should Work:

1. **Modal Display**
   - Opens immediately (admin) or after brief loading (billing page)
   - No blur effect on background
   - All bill details visible
   - Proper formatting

2. **Print Window**
   - Opens in new window
   - White background (forced)
   - Professional styling
   - Company branding
   - All bill information included

3. **Print Output**
   - Clean, professional appearance
   - White background in print preview
   - Readable text
   - Proper table borders
   - All details present

### ❌ What Should NOT Happen:

1. **No Blur**: Background should not blur when viewing bills
2. **No Loading Issues**: Bills should load quickly and display immediately
3. **No Missing Details**: All products, quantities, prices should be visible
4. **No Gray Background**: Print should have white background, not gray
5. **No Errors**: No console errors or failed requests

---

## Troubleshooting

### If Bill Modal Doesn't Open:
- Check browser console for errors (F12)
- Verify you're logged in
- Ensure bills exist in the system

### If Print Window is Blank:
- Wait a moment for content to load
- Check if popup blocker is enabled
- Try clicking print button again

### If Background is Not White:
- This should not happen - the styles force white background
- If it does, check browser print settings
- Ensure "Background graphics" is enabled in print settings

---

## Test Data

### Sample Bills Available:
- 14 sample bills created across different stores
- Bills from Mumbai, Delhi, Bangalore, Grocery stores
- Various dates and amounts
- Multiple products per bill

### Test Users:
- **Admin**: `admin` / `admin123`
- **Mumbai Store**: `mumbai_store` / `mumbai123`
- **Delhi Store**: `delhi_store` / `delhi123`
- **Bangalore Store**: `bangalore_store` / `bangalore123`

---

## Success Criteria

✅ All tests pass
✅ Bills display correctly
✅ Print has white background
✅ All details visible
✅ No errors or issues

**Status**: Ready for testing
**Date**: February 10, 2026
