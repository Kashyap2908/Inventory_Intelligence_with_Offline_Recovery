# NeuroStock AI - Persistent Login Feature

## Overview
The NeuroStock AI Smart Inventory System now includes **persistent login sessions** that keep users logged in until they manually logout, providing a seamless user experience.

## How It Works

### 1. **Automatic Dashboard Redirect**
- When users visit the website (`neurostock.local:8000` or `localhost:8000`), the system automatically checks if they're already logged in
- If logged in, users are immediately redirected to their role-based dashboard:
  - **Inventory Manager** → Inventory Dashboard
  - **Marketing Manager** → Trend Dashboard  
  - **Admin** → Admin Dashboard
- If not logged in, users see the login page

### 2. **Session Duration Options**

#### **Remember Me Checkbox (30 Days)**
- When users check "Keep me logged in for 30 days" during login
- Session lasts for 30 days even if browser is closed
- Perfect for personal devices

#### **Standard Login (7 Days)**
- When users don't check the remember me option
- Session lasts for 7 days minimum
- More secure for shared devices

#### **New User Auto-Login**
- New users who create accounts are automatically logged in for 30 days
- No need to login again after signup

### 3. **Session Security Features**

#### **Session Configuration**
```python
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days maximum
SESSION_SAVE_EVERY_REQUEST = True        # Extend session on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep session after browser close
SESSION_COOKIE_HTTPONLY = True           # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'          # CSRF protection
```

#### **Automatic Session Extension**
- Every time a user interacts with the system, their session is automatically extended
- Prevents unexpected logouts during active use

### 4. **User Experience Flow**

#### **First Time Users**
1. Visit website → See login page
2. Click "Create New Account" → Fill signup form
3. After signup → Automatically logged in and redirected to role dashboard
4. Next visit → Directly go to dashboard (no login needed)

#### **Returning Users**
1. Visit website → Automatically redirected to their dashboard
2. Continue working seamlessly
3. Only need to login again after 7-30 days (depending on remember me choice)

#### **Manual Logout**
1. Click logout button in any dashboard
2. Session is terminated
3. Next visit → Must login again

### 5. **Technical Implementation**

#### **Home View Logic**
```python
def home_view(request):
    if request.user.is_authenticated:
        # User is logged in - redirect to their dashboard
        profile = request.user.userprofile
        if profile.role == 'inventory':
            return redirect('inventory_dashboard')
        elif profile.role == 'marketing':
            return redirect('trend_dashboard')
        elif profile.role == 'admin':
            return redirect('admin_dashboard')
    else:
        # User not logged in - show login page
        return render(request, 'login.html')
```

#### **Enhanced Login Function**
- Checks if user is already logged in before showing login form
- Sets appropriate session duration based on "Remember Me" checkbox
- Provides seamless redirect to role-based dashboard

#### **Enhanced Signup Function**
- Auto-login after successful account creation
- Sets 30-day session for new users
- Immediate redirect to appropriate dashboard

### 6. **URL Structure**
- **`/`** → Home view (handles persistent login logic)
- **`/login/`** → Login page (if not already logged in)
- **`/signup/`** → Signup page (if not already logged in)
- **`/logout/`** → Logout and redirect to home
- **`/inventory/`** → Inventory Dashboard (login required)
- **`/trends/`** → Marketing Dashboard (login required)
- **`/admin-panel/`** → Admin Dashboard (login required)

### 7. **Benefits**

#### **For Users**
- ✅ No repeated login prompts
- ✅ Seamless access to their dashboard
- ✅ Choice of session duration (7 or 30 days)
- ✅ Automatic redirect to appropriate role dashboard
- ✅ Secure session management

#### **For Administrators**
- ✅ Improved user experience and adoption
- ✅ Reduced support requests about login issues
- ✅ Secure session handling with proper expiration
- ✅ Activity-based session extension

### 8. **Security Considerations**

#### **Session Security**
- Sessions are secured with HttpOnly cookies (prevent XSS)
- CSRF protection with SameSite cookie policy
- Automatic session expiration after inactivity period
- Secure session storage in Django's session framework

#### **Logout Security**
- Manual logout completely terminates the session
- Session data is cleared from server
- User must login again after logout

### 9. **Testing the Feature**

#### **Test Persistent Login**
1. Create a new account or login with existing account
2. Check "Keep me logged in for 30 days" (optional)
3. Close browser completely
4. Reopen browser and visit the website
5. Should automatically redirect to your dashboard

#### **Test Role-Based Redirect**
1. Login as different roles (inventory, marketing, admin)
2. Each should redirect to their specific dashboard
3. Verify correct dashboard loads for each role

#### **Test Logout**
1. Click logout button in any dashboard
2. Should redirect to home page showing login form
3. Verify session is terminated (no auto-login on next visit)

### 10. **Troubleshooting**

#### **If Auto-Login Doesn't Work**
- Check if cookies are enabled in browser
- Verify session hasn't expired (7-30 days)
- Clear browser cache and cookies if needed
- Check if user profile exists and has valid role

#### **If Wrong Dashboard Loads**
- Verify user profile role is set correctly
- Check UserProfile model in admin panel
- Ensure role is one of: 'inventory', 'marketing', 'admin'

## Conclusion

The persistent login feature significantly improves the user experience by eliminating repetitive login prompts while maintaining security through proper session management. Users can now focus on their inventory management tasks without authentication interruptions.

**Key Feature**: Once you create an account or login, you stay logged in until you manually logout - making the system truly user-friendly for daily operations.