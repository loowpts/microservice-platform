from django import forms
from django.core.exceptions import ValidationError

from .models import Gig, GigPackage


class GigForm(forms.ModelForm):
    class Meta:
        model = Gig
        fields = ['category', 'subcategory', 'title', 'description', 'main_image']

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or not (10 <= len(title) <= 200):
            raise ValidationError('Заголовок должен быть от 10 до 200 символов.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not (50 <= len(description) <= 5000):
            raise ValidationError('Описание должно быть от 50 до 5000 символов.')
        return description

class GigPackageForm(forms.ModelForm):
    class Meta:
        model = GigPackage
        fields = ['package_type', 'name', 'description', 'price', 'delivery_time', 'revisions', 'features']
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is None or price <= 0:
            raise ValidationError('Цена должна быть больше 0')
        if price > 1000000:
            raise ValidationError('Цена не может превышать 1 000 000')
        return price
    
    def clean_delivery_time(self):
        delivery_time = self.cleaned_data.get('delivery_time')
        if delivery_time is None or not (1 <= delivery_time <= 365):
            raise ValidationError('Срок должен быть от 1 до 365 дней')
        return delivery_time
    
    def clean_revisions(self):
        revisions = self.cleaned_data.get('revisions')
        if revisions is None or revisions < 0:
            raise ValidationError('Количество правок не может быть отрицательным')
        return revisions
