from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image_url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок поста'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Содержание поста',
                'rows': 10
            }),
            'image_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/image.jpg'
            }),
        }
        labels = {
            'title': 'Заголовок',
            'content': 'Содержание',
            'image_url': 'URL изображения',
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if len(title) < 5:
            raise forms.ValidationError('Заголовок слишком короткий.')
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise forms.ValidationError('Содержание поста должно содержать минимум 10 символов')
        return content


class PostSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск постов...'
        }),
        label='Поиск'
    )
    
    channel = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Фильтр по каналу'
        }),
        label='Канал'
    )
