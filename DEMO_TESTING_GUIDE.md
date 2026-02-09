# NeuroStock - Demo Testing Guide

## 🎯 Clean Demo Data Setup

Database has been reset with clean, minimal data for easy testing.

---

## 👥 DEMO USERS

### 1. Admin User
```
Username: admin
Password: admin123
Role: Administrator
Access: All features (4 tabs)
```

### 2. Mumbai Store (Inventory)
```
Username: mumbai_store
Password: mumbai123
Name: Raj Sharma
Store: Mumbai Store
Location: Andheri West, Mumbai, Maharashtra
Access: Inventory + Billing (2 tabs)
```

### 3. Delhi Store (Inventory)
```
Username: delhi_store
Password: delhi123
Name: Priya Singh
Store: Delhi Store
Location: Connaught Place, New Delhi
Access: Inventory + Billing (2 tabs)
```

### 4. Bangalore Store (Inventory)
```
Username: bangalore_store
Password: bangalore123
Name: Amit Kumar
Store: Bangalore Store
Location: Koramangala, Bangalore, Karnataka
Access: Inventory + Billing (2 tabs)
```

---

## 📦 DEMO PRODUCTS (10 Items)

All products have expiry dates for realistic testing:

1. **Basmati Rice 5kg** - Groceries (₹250/₹350)
2. **Wheat Flour 10kg** - Groceries (₹300/₹400)
3. **Sugar 1kg** - Groceries (₹40/₹50)
4. **Cooking Oil 1L** - Groceries (₹120/₹150)
5. **Milk 1L** - Dairy (₹50/₹60)
6. **Butter 500g** - Dairy (₹200/₹250)
7. **Bread Loaf** - Bakery (₹30/₹40)
8. **Eggs (12 pcs)** - Dairy (₹60/₹80)
9. **Biscuits Pack** - Snacks (₹20/₹30)
10. **Instant Noodles** - Snacks (₹12/₹20)

---

## 📊 STOCK DISTRIBUTION

### Mumbai Store (Raj Sharma):
- Basmati Rice 5kg: 50 units (Expires: Aug 2026)
- Wheat Flour 10kg: 60 units (Expires: Sep 2026)
- Sugar 1kg: 70 units (Expires: Oct 2026)
- Cooking Oil 1L: 80 units (Expires: Nov 2026)

**Total: 260 units across 4 products**

### Delhi Store (Priya Singh):
- Cooking Oil 1L: 40 units (Expires: Jul 2026)
- Milk 1L: 55 units (Expires: Aug 2026)
- Butter 500g: 70 units (Expires: Sep 2026)
- Bread Loaf: 85 units (Expires: Oct 2026)

**Total: 250 units across 4 products**

### Bangalore Store (Amit Kumar):
- Bread Loaf: 60 units (Expires: Jun 2026)
- Eggs (12 pcs): 70 units (Expires: Jul 2026)
- Biscuits Pack: 80 units (Expires: Aug 2026)
- Instant Noodles: 90 units (Expires: Sep 2026)

**Total: 300 units across 4 products**

---

## 🧪 TESTING SCENARIOS

### Scenario 1: View User Identity
**Steps:**
1. Login as `mumbai_store` (password: mumbai123)
2. Check top-right navbar
3. **Expected:** See "Raj Sharma" and "Mumbai Store"

### Scenario 2: View User-Specific Stock
**Steps:**
1. Login as `mumbai_store`
2. Go to Products Overview tab
3. **Expected:** 
   - "My Stock" shows Mumbai's stock only
   - "Total Stock" shows combined stock from all stores

### Scenario 3: Admin Views All Stock
**Steps:**
1. Login as `admin` (password: admin123)
2. Go to Admin Dashboard → Inventory Stock Overview tab
3. **Expected:**
   - See all 10 products
   - Each product shows stock distribution by store
   - Percentage calculations for each user

### Scenario 4: Product Request Workflow
**Steps:**
1. Login as `delhi_store` (password: delhi123)
2. Go to Add Items → Request Product from Admin
3. Select "Basmati Rice 5kg" (not in Delhi stock)
4. Request 30 units
5. **Expected:** Clean notification sent to admin

**Admin Side:**
1. Login as `admin`
2. Go to Admin Dashboard → Actions & Orders
3. **Expected:** See request from "Priya Singh (Delhi Store)"
4. Approve 30 units
5. **Expected:** 
   - Stock deducted from Mumbai (FEFO)
   - Bill auto-generated
   - Delhi user notified

**Delhi User:**
1. Login back as `delhi_store`
2. Check notifications
3. **Expected:** Clean, single-line approval notification
4. Go to Billing tab
5. **Expected:** See auto-generated bill

### Scenario 5: Add New Stock
**Steps:**
1. Login as `bangalore_store`
2. Go to Add Items → Add Stock
3. Add: Milk 1L, 40 units, Expiry: Dec 2026
4. **Expected:**
   - Stock added to Bangalore store
   - Success message shows user's stock count
   - Admin can see it in Stock Overview

### Scenario 6: Notification Format
**Steps:**
1. Create any product request
2. Check notification
3. **Expected:**
   - Single-line format
   - All info visible: From, Product, Qty, Price, Date
   - No paragraph breaks
   - Easy to scan

---

## ✅ VERIFICATION CHECKLIST

### User Identity:
- [ ] Navbar shows user name
- [ ] Navbar shows store name (inventory users)
- [ ] Admin shows "Administrator" badge

### Stock Management:
- [ ] Each user sees only their stock in "My Stock"
- [ ] Total stock shows combined from all users
- [ ] Admin sees complete distribution

### Product Requests:
- [ ] Request form works
- [ ] Admin receives clean notification
- [ ] Notification shows store name
- [ ] Approval generates bill
- [ ] Stock deducted correctly (FEFO)

### Notifications:
- [ ] Single-line format
- [ ] All information visible
- [ ] Store name included
- [ ] Easy to read

### Expiry Dates:
- [ ] All products have expiry dates
- [ ] Expiry dates visible in stock entries
- [ ] FEFO logic works (oldest first)

---

## 🔄 RESET DATABASE AGAIN

If you want to reset to clean demo data again:

```bash
python reset_demo_data.py
```

This will:
- Delete all old data
- Keep admin user
- Create 3 fresh inventory users
- Create 10 products
- Add sample stock

---

## 📊 EXPECTED RESULTS

### After Testing:

**Products:** 10 essential items
**Users:** 1 admin + 3 inventory stores
**Stock Entries:** 12 (distributed across stores)
**Orders:** 0 (fresh start)
**Bills:** 0 (will be created during testing)

### Stock Distribution:
- Mumbai: 260 units (4 products)
- Delhi: 250 units (4 products)
- Bangalore: 300 units (4 products)
- **Total Company Stock:** 810 units

### Overlapping Products:
- Cooking Oil: Mumbai (80) + Delhi (40) = 120 units total
- Bread Loaf: Delhi (85) + Bangalore (60) = 145 units total

This shows multi-store inventory clearly!

---

## 🎯 KEY FEATURES TO TEST

1. **User Identity Display** ✅
   - Name and store in navbar
   - Store info in notifications

2. **User-Specific Stock** ✅
   - My Stock vs Total Stock
   - Admin sees all distributions

3. **Product Requests** ✅
   - Clean notification format
   - Store identification
   - Auto-billing

4. **Expiry Management** ✅
   - All products have expiry dates
   - FEFO logic in action
   - Expiry tracking

5. **Multi-Store Support** ✅
   - 3 different stores
   - Separate stock tracking
   - Combined reporting

---

## 🚀 QUICK START

1. **Start Server:**
   ```bash
   python manage.py runserver
   ```

2. **Access:** http://127.0.0.1:8000/

3. **Login as Mumbai Store:**
   - Username: `mumbai_store`
   - Password: `mumbai123`

4. **Test Features:**
   - View your stock
   - Request a product
   - Check notifications

5. **Login as Admin:**
   - Username: `admin`
   - Password: `admin123`

6. **Admin Actions:**
   - View all stores' stock
   - Approve requests
   - Check distributions

---

**Clean, minimal data for easy testing!** ✨
