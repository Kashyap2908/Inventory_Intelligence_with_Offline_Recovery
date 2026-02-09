# Inventory Product Request & Auto-Billing System

## Overview
Complete workflow system where inventory users can request products from admin, admin approves and sends the quantity, and bills are automatically generated.

## Workflow

### 1. Inventory User Requests Product
**Location:** Inventory Dashboard → Add Items Tab → "Request Product from Admin" Form

**Process:**
- Inventory user selects a product from dropdown
- Enters the quantity needed
- Clicks "Send Request"
- Request is sent to admin with all product details

**What Happens:**
- OrderQueue entry created with `requested_by` = inventory user
- Status set to 'pending'
- Admin receives high-priority notification with:
  - Requester name
  - Product name and category
  - Requested quantity
  - Current stock level
  - Cost and selling prices
  - Request timestamp

### 2. Admin Reviews Request
**Location:** Admin Dashboard → Actions & Orders Tab → "Product Requests from Inventory" Section

**Admin Sees:**
- Requester name
- Product details (name, category, prices)
- Requested quantity
- Available stock (color-coded: green if sufficient, red if insufficient)
- Request date and time

**Admin Actions:**
- Reviews available stock
- Enters approved quantity (can be same or different from requested)
- Clicks "Approve & Send Product"

### 3. Automatic Processing
**When Admin Approves:**

**a) Order Request Updated:**
- `approved_quantity` field set
- Status changed to 'approved'
- Timestamp recorded

**b) Bill Auto-Generated:**
- Bill number: `BILL-YYYYMMDDHHMMSS`
- Created for the inventory user who requested
- Contains:
  - Product details
  - Approved quantity
  - Selling price
  - Total amount
- Bill linked to order request

**c) Stock Deducted (FEFO Logic):**
- Stock deducted using First Expired, First Out
- Oldest expiry dates used first
- Stock entries updated automatically

**d) Inventory User Notified:**
- High-priority notification sent
- Contains:
  - Approved quantity
  - Bill number
  - Total amount
  - Current stock level
- Notification appears in inventory dashboard

### 4. Inventory User Receives Confirmation
**Location:** Inventory Dashboard → Notifications Tab

**User Sees:**
- Approval notification with all details
- Bill automatically added to their Billing section
- Can view bill details in Billing tab

## Database Schema

### OrderQueue Model (Enhanced)
```python
- product: ForeignKey to Product
- quantity: Requested quantity
- approved_quantity: Admin-approved quantity (nullable)
- status: 'pending', 'approved', 'ordered', 'received', 'completed'
- requested_by: Inventory user who requested (nullable)
- ordered_by: Admin who created order (nullable)
- bill_generated: Boolean flag
- bill: Link to generated SalesBill (nullable)
- created_at, updated_at: Timestamps
```

### SalesBill Model
```python
- bill_number: Unique identifier
- created_by: User who the bill is for
- total_amount: Total bill amount
- created_at: Timestamp
```

### SalesBillItem Model
```python
- bill: ForeignKey to SalesBill
- product: ForeignKey to Product
- quantity: Quantity sold
- price: Unit price
- total: Line item total
```

## Features

### For Inventory Users:
✅ Easy product request form with dropdown selection
✅ Real-time request status tracking
✅ Automatic bill generation
✅ Notification when request is approved
✅ Bills appear in their Billing section automatically

### For Admin:
✅ Clear view of all pending requests
✅ Stock availability check before approval
✅ Flexible quantity approval (can send less/more than requested)
✅ Automatic stock deduction with FEFO logic
✅ Automatic bill generation
✅ Request tracking and history

### System Benefits:
✅ Eliminates manual bill creation
✅ Ensures accurate stock tracking
✅ Maintains FEFO compliance
✅ Complete audit trail
✅ Real-time notifications
✅ User-specific billing records

## User Interface

### Inventory Dashboard - Request Form:
- Clean, intuitive form layout
- Product dropdown with category display
- Quantity input with validation
- Info alert explaining the workflow
- Warning-themed card (yellow) for visibility

### Admin Dashboard - Request Cards:
- Card-based layout for each request
- Color-coded stock availability
- All relevant information at a glance
- Simple approval form with quantity input
- Success confirmation after approval

## Technical Implementation

### Views:
- `inventory_dashboard`: Handles product request creation
- `admin_dashboard`: Handles request approval and processing

### URL Endpoints:
- POST to inventory dashboard with `request_product` parameter
- POST to admin dashboard with `approve_product_request` parameter

### Notifications:
- High-priority admin notification on request
- High-priority inventory notification on approval
- Detailed information in both notifications

### Stock Management:
- FEFO logic implemented
- Automatic stock entry updates
- Real-time stock level tracking

## Migration Applied
- Migration 0011: Added new fields to OrderQueue model
  - approved_quantity
  - requested_by
  - bill_generated
  - bill (ForeignKey)
  - Updated status choices

## Testing Checklist
- [x] Inventory user can request products
- [x] Admin receives notification
- [x] Admin can see request details
- [x] Admin can approve with custom quantity
- [x] Bill is auto-generated
- [x] Stock is deducted correctly (FEFO)
- [x] Inventory user receives notification
- [x] Bill appears in user's billing section
- [x] All timestamps recorded correctly
- [x] Server runs without errors

## Future Enhancements (Optional)
- Request rejection with reason
- Partial fulfillment tracking
- Request history view
- Bulk request approval
- Email notifications
- SMS alerts for urgent requests
