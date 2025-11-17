from django import forms
from .models import CustomProposal, PROPOSAL_STATUS_CHOICES

class ProposalForm(forms.ModelForm):
    class Meta:
        model = CustomProposal
        fields = [
            'title', 'description', 'price',
            'delivery_days', 'revisions', 'buyer_message'
        ]

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 10:
            raise forms.ValidationError('Заголовок должен быть минимум 10 символов.')
        if len(title) > 200:
            raise forms.ValidationError('Заголовок должен быть максимум 200 символов.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 50:
            raise forms.ValidationError('Описание должно быть минимум 50 символов.')
        if len(description) > 2000:
            raise forms.ValidationError('Описание должно быть максимум 2000 символов.')
        return description
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        
        if price is None:
            raise forms.ValidationError('Цена обязательна.')
        if price <= 0:
            raise forms.ValidationError('Цена должна быть больше нуля.')
        if price > 1000000:
            raise forms.ValidationError('Цена не может превышать 1,000,000.')
        
        return price
    
    def clean_delivery_days(self):
        delivery_days = self.cleaned_data.get('delivery_days')
        
        if delivery_days is None:
            raise forms.ValidationError('Срок доставки обязателен.')
        if not (1 <= delivery_days <= 365):
            raise forms.ValidationError('Срок должен быть от 1 до 365 дней.')
        
        return delivery_days

    def clean_revisions(self):
        revisions = self.cleaned_data.get('revisions')
        if revisions is None:
            raise forms.ValidationError('Количество правок обязательно.')
        if revisions < 0:
            raise forms.ValidationError('Количество правок не может быть отрицательным.')
        return revisions
    
    
    
