from typing import Any
from django import forms
from .models import Product, ProductImage

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'title', 'description', 'price', 'old_price',
            'category', 'condition', 'city', 'quantity' 
            ]
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price <= 0:
            raise forms.ValidationError('Цена должна быть больше 0')
        return price
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        
        if len(title) < 5:
            raise forms.ValidationError('Название слишком короткое.')
        return title
    
    def clean(self):
        cleaned_data = super().clean()
        old_price = self.cleaned_data.get('old_price')
        price = self.cleaned_data.get('price')

        if old_price:
            if old_price <= price:
                raise forms.ValidationError('Старая цена должна быть больше новой')
        return cleaned_data

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image_url', 'order']
    
            