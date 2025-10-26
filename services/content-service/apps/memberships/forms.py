from django import forms
from .models import ChannelMembership


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
