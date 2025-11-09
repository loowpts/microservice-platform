from django import forms
from .models import Review
from django.core.exceptions import ValidationError


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'pros', 'cons']
        
    
    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        
        if rating is None:
            raise ValidationError('Нужно выбрать оценку.')
        elif not (1 <= rating <= 5):
            raise ValidationError('Оценка должна быть от 1 до 5')
        
        return rating
    
    def clean_comment(self):
        comment = self.cleaned_data.get('comment')
        
        if not comment or len(comment) < 10:
            raise ValidationError('Отзыв должен содержать минимум 10 символов')
        return comment

    def clean_pros(self):
        pros = self.cleaned_data.get('pros')
        
        if pros and len(pros) < 5:
            raise ValidationError('Описание "плюсов" должно содержать хотя бы 5 символов.')
        return pros

    def clean_cons(self):
        cons = self.cleaned_data.get('cons')
        
        if cons and len(cons) < 5:
            raise ValidationError('Описание "минусов" должно содержать хотя бы 5 символов.')
        return cons
    
