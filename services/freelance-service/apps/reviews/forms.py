from typing import Any
from django import forms
from .models import Review, ReviewReply
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = [
            'rating', 'comment', 'communication_rating',
            'service_quality_rating', 'delivery_rating'
        ]

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating or not (1 <= rating <=5):
            raise forms.ValidationError('Оценка должна быть от 1 до 5')
        return rating
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        if len(comment) < 10:
            raise forms.ValidationError('Комментарий должен быть минимум 10 символов.')
        if len(comment) > 2000:
            raise forms.ValidationError('Комментарий должен быть максимум 2000 символов.')
        return comment
    
    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        
        rating_fields = [
            'communication_rating',
            'service_quality_rating',
            'delivery_rating'
        ]

        for field in rating_fields:
            value = cleaned_data.get(field)
            
            if value is not None:
                if not (1 <= value <= 5):
                    raise forms.ValidationError({
                        field: 'Оценка должна быть от 1 до 5'
                    })
        return cleaned_data

class ReviewReplyForm(forms.ModelForm):
    class Meta:
        model = ReviewReply
        fields = ['message']
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError('Сообщение должно быть минимум 10 символов.')
        if len(message) > 1000:
            raise forms.ValidationError('Сообщение должно быть максимум 1000 символов.')
        return message    
