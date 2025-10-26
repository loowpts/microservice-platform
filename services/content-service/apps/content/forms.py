from django import forms
from .models import Channel


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
