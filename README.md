# NeuroStock AI - Smart Inventory Management System

![NeuroStock AI](https://img.shields.io/badge/NeuroStock-AI%20Powered-blue?style=for-the-badge&logo=brain&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2.7-green?style=for-the-badge&logo=django)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![AI](https://img.shields.io/badge/Google%20Gemini-AI%20Integration-orange?style=for-the-badge&logo=google)

## 🧠 **AI-Powered Smart Inventory Management System**

NeuroStock AI is a comprehensive inventory management system that combines traditional inventory control with cutting-edge artificial intelligence for market trend analysis and intelligent decision-making.

## ✨ **Key Features**

### 🎯 **Core Functionality**
- **Smart Inventory Management** - FEFO (First Expired, First Out) logic
- **Role-Based Access Control** - Admin, Inventory Manager, Marketing Analyst
- **Real-Time Notifications** - Expiry warnings, low stock alerts
- **Professional Billing System** - Complete POS functionality
- **Automatic Expiry Management** - Daily cleanup of expired products

### 🤖 **AI-Powered Features**
- **Google Gemini AI Integration** - Real market trend analysis
- **Intelligent Trend Scoring** - 0-10 scale market demand prediction
- **Smart Recommendations** - AI-driven pricing and stock suggestions
- **Market Intelligence** - Real-time demand forecasting

### 🎨 **User Experience**
- **NeuroStock Branding** - Professional AI-themed design
- **Real-Time Clocks** - Live time display across all dashboards
- **Responsive Design** - Mobile and desktop optimized
- **Clean Interface** - Modern, professional UI/UX
- **QR Code System** - Individual bill QR codes for instant access
- **CSV Bulk Billing** - Upload shop owner restock orders via CSV

### 📱 **QR Code Features**
- **Individual Bill QR Codes** - Each bill has unique QR code
- **Instant Bill Access** - Scan to view complete bill details
- **Offline Capability** - Works without internet after first load
- **No Login Required** - Public access to bill information
- **Privacy Protected** - Each QR shows only that specific bill

## 🚀 **Quick Start**

### **Prerequisites**
- Python 3.8+
- Django 4.2.7
- SQLite3 (included with Python)
- Google Gemini AI API Key (optional)

### **Installation**

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/neurostock-inventory-system.git
cd neurostock-inventory-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup database**
```bash
python manage.py migrate
```

4. **Create superuser (optional)**
```bash
python manage.py createsuperuser
```

5. **Run the server**
```bash
python manage.py runserver
```

6. **Access the application**
- Open browser: `http://localhost:8000`
- Create your account or use demo credentials

## 👥 **User Roles & Access**

### 📦 **Inventory Manager**
- Product management (add, edit, delete)
- Stock entry and tracking
- Expiry date monitoring
- Notification management
- FEFO stock deduction
- CSV bulk billing for shop restock orders

### 📊 **Marketing Analyst**
- AI trend analysis dashboard
- Market intelligence reports
- Demand forecasting
- Pricing recommendations
- Real-time trend scoring

### 🔧 **System Administrator**
- Complete system access
- User management
- System notifications
- Order management
- Billing oversight

## 🤖 **AI Integration**

### **Google Gemini AI Setup**
1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create `config.py` in project root:
```python
GOOGLE_API_KEY = "your-api-key-here"
```
3. AI will automatically analyze market trends when you click "Run Trend Analysis"

### **Intelligent Simulation Fallback**
- If AI is unavailable, system uses intelligent simulation
- Considers product category, stock levels, seasonality
- Provides realistic trend scores and recommendations

## 📱 **Mobile Access**

### **Network Setup**
```bash
# Run server for network access
python manage.py runserver 0.0.0.0:8000

# Access from mobile
http://YOUR_IP_ADDRESS:8000
```

## 📱 **QR Code System**

### **Individual Bill QR Codes**
Each bill automatically generates a unique QR code that provides instant access to complete bill details.

### **Features**
- **Automatic Generation** - QR code created when bill is printed
- **Individual Access** - Each QR shows only that specific bill
- **Complete Details** - Product breakdown, quantities, prices
- **Store Information** - Store name, location, seller details
- **Offline Capable** - Works without internet after first load
- **No Login Required** - Public access for customers
- **Privacy Protected** - No access to other bills

### **How It Works**
1. **Create Bill** - Generate bill in billing system
2. **Print Bill** - QR code appears at bottom of printed bill
3. **Customer Scans** - Opens individual bill page
4. **View Details** - See complete product breakdown

### **QR Code URL Format**
```
http://localhost:8000/bill/<BILL_NUMBER>/
```

### **Example**
```
Bill: BILL-20260210141502
QR URL: http://localhost:8000/bill/BILL-20260210141502/
Shows: Only this bill's details with all products
```

### **Setup QR Tokens**
```bash
# Create QR tokens for all users
python manage.py shell
from inventory.models import QRToken, UserProfile
for profile in UserProfile.objects.all():
    QRToken.objects.get_or_create(user_profile=profile)
```

### **Testing**
```bash
# Test individual bill QR system
python test_individual_bill_qr.py
```

### **Documentation**
- **INDIVIDUAL_BILL_QR_COMPLETE.md** - Complete guide
- **QR_QUICK_START.md** - Quick reference

## 📄 **CSV Bulk Billing**

### **Overview**
The CSV Bulk Billing feature allows inventory managers to quickly create bills by uploading CSV files containing shop owner restock orders. This streamlines the process of handling bulk orders from multiple shop owners.

### **How It Works**
1. **Shop Owner Creates CSV** - Shop owner prepares a CSV file with products they want to restock
2. **Upload to System** - Inventory manager uploads the CSV through the billing page
3. **Automatic Processing** - System validates products, checks stock, and creates bill
4. **Inventory Deduction** - Stock automatically deducted using FEFO method

### **CSV Format**
```csv
product_name,quantity
Rice,50
Sugar,30
Wheat Flour,40
Cooking Oil,25
```

### **Features**
- ✅ Bulk order processing in seconds
- ✅ Automatic stock validation
- ✅ FEFO inventory deduction
- ✅ Error handling with detailed messages
- ✅ Partial processing (valid products processed even if some fail)
- ✅ Automatic bill generation
- ✅ Notification system integration

### **Usage**
1. Go to Billing page
2. Find "CSV Bulk Billing" section
3. Upload CSV file with shop owner's order
4. System creates bill and deducts inventory
5. Review success/error messages

### **Sample Files**
- `sample_restock_order.csv` - Template for shop owners
- `CSV_BILLING_GUIDE.md` - Complete documentation

### **Benefits**
- **Speed**: Process 50+ products in seconds vs manual entry
- **Accuracy**: Reduces manual entry errors
- **Automation**: Automatic inventory management
- **Tracking**: All orders tracked with unique bill numbers
- **Scalability**: Handle multiple shop owners efficiently

## 🔐 **Security Features**

- **CSRF Protection** - All forms protected
- **Role-Based Access** - Secure dashboard routing  
- **Input Validation** - Comprehensive form validation
- **Password Security** - Django's built-in hashing
- **Session Management** - Secure user sessions

## 📊 **System Architecture**

```
NeuroStock AI
├── Authentication System (Username/Password)
├── Role-Based Dashboards
│   ├── Inventory Dashboard
│   ├── Marketing Trend Dashboard
│   └── Admin Dashboard
├── AI Integration Layer
│   ├── Google Gemini API
│   └── Intelligent Simulation
├── QR Code System
│   ├── Individual Bill QR Generation
│   ├── Offline Bill Access
│   └── Public Bill Viewing
├── Core Features
│   ├── Product Management
│   ├── Stock Control (FEFO)
│   ├── Billing System
│   └── Notification System
└── Real-Time Features
    ├── Live Clocks
    ├── Trend Updates
    └── Notification Alerts
```

## 🛠️ **Technology Stack**

- **Backend**: Django 4.2.7, Python 3.8+
- **Database**: SQLite3 (production-ready)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI**: Google Gemini API
- **QR Codes**: qrcode, Pillow, QRCode.js
- **Real-Time**: AJAX, WebSocket-ready
- **Styling**: Professional CSS with animations

## 📈 **Features Overview**

### **Inventory Management**
- ✅ Product CRUD operations
- ✅ Stock entry with expiry dates
- ✅ FEFO automatic deduction
- ✅ Low stock alerts
- ✅ Expiry warnings

### **AI Trend Analysis**
- ✅ Real-time market analysis
- ✅ Trend scoring (0-10 scale)
- ✅ Smart recommendations
- ✅ Demand forecasting
- ✅ Price optimization

### **Billing & Sales**
- ✅ Complete POS system
- ✅ CSV bulk billing for shop restock orders
- ✅ Real-time stock deduction
- ✅ Sales reporting
- ✅ Monthly analytics
- ✅ Bill management
- ✅ Individual bill QR codes
- ✅ Offline bill access

### **QR Code System**
- ✅ Automatic QR generation per bill
- ✅ Scan to view bill details
- ✅ Product breakdown table
- ✅ Store information display
- ✅ Works offline
- ✅ No login required
- ✅ Print-friendly design

### **User Management**
- ✅ Role-based access
- ✅ Secure authentication
- ✅ Profile management
- ✅ Activity tracking

## 🎯 **Getting Started Guide**

### **For New Users**
1. Visit the application URL
2. Click "Create New Account"
3. Fill in your details and select role
4. You'll be automatically logged in
5. Access your role-specific dashboard

### **For Existing Users**
1. Login with your username and password
2. Access your dashboard based on your role
3. Start managing inventory or analyzing trends

## 🔄 **Workflow Examples**

### **Inventory Manager Workflow**
```
Login → Inventory Dashboard → Add Products → Enter Stock → 
Monitor Notifications → Process Sales → Track Expiry
```

### **Marketing Analyst Workflow**
```
Login → Trend Dashboard → Run AI Analysis → Review Scores → 
Apply Recommendations → Monitor Market Changes
```

### **Admin Workflow**
```
Login → Admin Dashboard → Manage Users → Send Notifications → 
Monitor System → Review Reports
```

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Google Gemini AI** for intelligent market analysis
- **Django Framework** for robust backend
- **Bootstrap** for responsive design
- **Font Awesome** for beautiful icons

## 📞 **Support**

For support, email support@neurostock.ai or create an issue in this repository.

---

**Made with ❤️ and 🧠 AI by the NeuroStock Team**