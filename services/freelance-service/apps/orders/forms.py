from django import forms
from .models import Order, OrderDelivery


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['requirements']
    
    def clean_requirements(self):
        requirements = self.cleaned_data.get('requirements', '').strip()
        if len(requirements) > 3000:
            return forms.ValidationError(
                'Требования не должно превышать 3000 символов.'
            )
            
        return requirements
        

class OrderDeliveryForm(forms.ModelForm):
    class Meta:
        model = OrderDelivery
        fields = ['message', 'file_url']
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError(
                'Сообщение должно быть минимум 10 символов.'
            )
            
        elif len(message) > 2000:
            raise forms.ValidationError(
                'Сообщение не должно превышать 2000 символов'
            )
            
        return message
    
    def clean_file_url(self):
        file_url = self.cleaned_data.get('file_url', '').strip()
        if not file_url:
            return None
        elif len(file_url) > 500:
            raise forms.ValidationError(
                'Длина URL слишом большая. (Максимальная длина не должна превышать 500 символов)'
            )
            
        return file_url
    
