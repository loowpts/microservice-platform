from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, UserProfile
import pytz

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Этот e-mail уже зарегегистрирован.')
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password1') != cleaned.get('password2'):
            self.add_error('password2', 'Пароли не совпадают.')
        return cleaned

    def save(self, commit=True):
        user = User(
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name']
        )
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    timezone = forms.ChoiceField(choices=[(tz, tz) for tz in pytz.all_timezones], required=False)

    class Meta:
        model = UserProfile
        fields = ('bio', 'avatar', 'is_public', 'timezone', 'streak_visibility')

    def clean(self):
        cleaned_data = super().clean()
        for field in ['is_public', 'streak_visibility']:
            if isinstance(cleaned_data.get(field), str):
                cleaned_data[field] = cleaned_data[field].lower() in ('true', '1', 't')
        return cleaned_data

class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="E-mail")
