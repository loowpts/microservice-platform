from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.partial = kwargs.pop('partial', False)
        super().__init__(*args, **kwargs)
        
        if self.partial:
            for field in self.fields.values():
                field.required = False

    class Meta:
        model = Post
        fields = ['title', 'content', 'image_url']
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        
        if self.partial and not title:
            return self.instance.title
        if not title:
            raise forms.ValidationError('Заголовок обязателен')
        if len(title) < 5:
            raise forms.ValidationError('Заголовок слишком короткий.')
        
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        if self.partial and not content:
            return self.instance.content
        if not content:
            raise forms.ValidationError('Содержание поста обязательно')  
        if len(content) < 10:
            raise forms.ValidationError('Содержание должно содержать минимум 10 символов')
        
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
