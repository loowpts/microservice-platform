from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите комментарий...',
                'rows': 3
            }),
        }
        labels = {
            'content': '',
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 2:
            raise forms.ValidationError('Комментарий cлишком короткий.')
        if len(content) > 1000:
            raise forms.ValidationError('Комментарий не может быть длиннее 1000 символов.')
        return content


class CommentReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content', 'parent']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Напишите ответ...',
                'rows': 2
            }),
            'parent': forms.HiddenInput(),
        }
        labels = {
            'content': '',
        }
