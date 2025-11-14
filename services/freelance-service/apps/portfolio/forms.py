from django import forms
from .models import PortfolioItem, PortfolioImage


class PortfolioItemForm(forms.ModelForm):
    class Meta:
        model = PortfolioItem
        fields = [
            'title', 'description', 'main_image',
            'project_url', 'technologies' ,'category'
        ]
        
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or not (5 <= len(title) <= 200):
            raise forms.ValidationError('Заголовок должен быть от 5 до 200 символов.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description or not (20 <= len(description) <= 2000):
            raise forms.ValidationError('Описание должно быть от 20 до 2000 символов.')
        return description
    
    def clean_project_url(self):
        project_url = self.cleaned_data.get('project_url')
        
        if project_url and not project_url.startswith(('http://', 'https://')):
            raise forms.ValidationError('Ссылка должна начинаться с http:// или https://')
        return project_url
        
    def clean_technologies(self):
        technologies = self.cleaned_data.get('technologies')
        
        if not technologies:
            return []

        if not isinstance(technologies, list):
            technologies = [technologies]
            
        for tech in technologies:
            if not isinstance(tech, str):
                raise forms.ValidationError(
                    'Каждый элемент в technologies должен быть строкой.'
                )    
        return technologies    
    
    
class PortfolioImageForm(forms.ModelForm):
    class Meta:
        model = PortfolioImage
        fields = ['image_url', 'order', 'caption']

    def clean_image_url(self):
        image_url = self.cleaned_data.get('image_url')
        
        if not image_url:
            raise forms.ValidationError('URL изображения обязателен')
        
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if not any(image_url.lower().endswith(ext) for ext in allowed_extensions):
            raise forms.ValidationError('URL должен вести на изображение (jpg, jpeg, png, gif, webp)')
        
        return image_url
