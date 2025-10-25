from django import forms
from .models import Channel, ChannelMembership, Post, Comment


class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название канала'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Описание канала',
                'rows': 4
            }),
        }
        labels = {
            'name': 'Название канала',
            'description': 'Описание',
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError('Название канала должно содержать минимум 3 символа')
        return name


class ChannelUpdateForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Описание канала',
                'rows': 4
            }),
        }
        labels = {
            'description': 'Описание',
        }


class ChannelMembershipForm(forms.ModelForm):
    class Meta:
        model = ChannelMembership
        fields = ['user_id', 'role']
        widgets = {
            'user_id': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'ID пользователя'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'user_id': 'ID пользователя',
            'role': 'Роль',
        }


class ChannelMembershipRoleForm(forms.ModelForm):
    class Meta:
        model = ChannelMembership
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'role': 'Роль',
        }


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


class ChannelSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск каналов...'
        }),
        label='Поиск'
    )
