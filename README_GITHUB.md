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
- ✅ Real-time stock deduction
- ✅ Sales reporting
- ✅ Monthly analytics
- ✅ Bill management

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