from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Product, ExpiryStock, OrderQueue, SalesBill, SalesBillItem, UserProfile, ShopOwner, RestockOrder

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        })
    )
    role = forms.ChoiceField(
        choices=[
            ('inventory', 'Inventory Manager'),
            ('marketing', 'Marketing Analyst'),
            ('admin', 'Admin'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Choose a username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Create user profile
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
        return user

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'cost_price', 'selling_price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class StockEntryForm(forms.ModelForm):
    product = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control product-autocomplete',
            'placeholder': 'Type product name...',
            'autocomplete': 'off'
        })
    )
    
    class Meta:
        model = ExpiryStock
        fields = ['product', 'quantity', 'expiry_date']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def clean_product(self):
        product_name = self.cleaned_data['product']
        try:
            product = Product.objects.get(name__iexact=product_name)
            return product
        except Product.DoesNotExist:
            raise forms.ValidationError(f"Product '{product_name}' not found. Please select from the dropdown.")

class OrderForm(forms.ModelForm):
    product = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control product-autocomplete',
            'placeholder': 'Type product name...',
            'autocomplete': 'off'
        })
    )
    
    class Meta:
        model = OrderQueue
        fields = ['product', 'quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean_product(self):
        product_name = self.cleaned_data['product']
        try:
            product = Product.objects.get(name__iexact=product_name)
            return product
        except Product.DoesNotExist:
            raise forms.ValidationError(f"Product '{product_name}' not found. Please select from the dropdown.")

class DiscountForm(forms.Form):
    product = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control product-autocomplete',
            'placeholder': 'Type product name...',
            'autocomplete': 'off'
        })
    )
    discount_percentage = forms.FloatField(widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '100'}))
    
    def clean_product(self):
        product_name = self.cleaned_data['product']
        try:
            product = Product.objects.get(name__iexact=product_name)
            return product
        except Product.DoesNotExist:
            raise forms.ValidationError(f"Product '{product_name}' not found. Please select from the dropdown.")

class SalesForm(forms.Form):
    product = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control product-autocomplete',
            'placeholder': 'Type product name...',
            'autocomplete': 'off'
        })
    )
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}))
    
    def clean_product(self):
        product_name = self.cleaned_data['product']
        try:
            product = Product.objects.get(name__iexact=product_name)
            return product
        except Product.DoesNotExist:
            raise forms.ValidationError(f"Product '{product_name}' not found. Please select from the dropdown.")

class StockReceiveForm(forms.Form):
    """Form for receiving ordered stock"""
    order = forms.ModelChoiceField(
        queryset=OrderQueue.objects.filter(status='ordered'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Select Order to Receive",
        empty_label="Choose an order..."
    )
    received_quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter received quantity'}),
        label="Received Quantity"
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Expiry Date"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show orders that are in "ordered" status and acknowledged
        self.fields['order'].queryset = OrderQueue.objects.filter(
            status='ordered',
            message_received=True
        ).select_related('product', 'ordered_by').order_by('-created_at')
        
        # Custom display for orders
        self.fields['order'].label_from_instance = self.order_label_from_instance
    
    def order_label_from_instance(self, obj):
        """Custom label for order dropdown"""
        return f"{obj.product.name} - {obj.quantity} units (Stock: {obj.product.total_stock}) - by {obj.ordered_by.first_name or obj.ordered_by.username}"
    
    def clean(self):
        cleaned_data = super().clean()
        order = cleaned_data.get('order')
        received_quantity = cleaned_data.get('received_quantity')
        
        if order and received_quantity:
            if received_quantity > order.quantity * 2:  # Allow up to 2x ordered quantity
                raise forms.ValidationError(
                    f"Received quantity ({received_quantity}) seems too high for ordered quantity ({order.quantity}). "
                    f"Please verify the amount."
                )
        
        return cleaned_data

class CSVBillingForm(forms.Form):
    """Form for uploading CSV file to create bills"""
    csv_file = forms.FileField(
        label="Upload CSV File",
        help_text="CSV should have columns: product_name, quantity",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )

class ShopOwnerForm(forms.ModelForm):
    """Form for adding shop owners"""
    class Meta:
        model = ShopOwner
        fields = ['name', 'shop_name', 'phone_number', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Owner name'}),
            'shop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shop name'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Shop address'}),
        }

class RestockOrderForm(forms.ModelForm):
    """Form for shop owners to upload restock orders"""
    class Meta:
        model = RestockOrder
        fields = ['shop_owner', 'csv_file', 'notes']
        widgets = {
            'shop_owner': forms.Select(attrs={'class': 'form-select'}),
            'csv_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes'}),
        }