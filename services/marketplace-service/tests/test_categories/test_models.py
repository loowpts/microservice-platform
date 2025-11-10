import pytest
from django.db import IntegrityError, transaction
from apps.categories.models import Category

@pytest.mark.django_db
class TestCategoryModel:

    def test_unique_name(self):
        """
        Задача:
        - Проверить, что поле `name` уникально.
        - При создании категории с одинаковым значением поля `name` должно возникать исключение.
        """
        
        Category.objects.create(
            name='Test Name',
            slug='test-name'
        )
        
        with pytest.raises(IntegrityError):
            Category.objects.create(
                name='Test Name',
                slug='test-name-2'
            )
        
    def test_slug_generation_on_create(self):
        """
        Задача:
        - Проверить, что при создании категории без указания `slug`, он генерируется автоматически на основе `name`.
        """
        category = Category.objects.create(
            name='Test Name',
        )
        
        assert category.slug == 'test-name'
    
    def test_unique_slug_generation(self):
        """
        Задача:
        - Проверить, что при создании категорий с одинаковым значением `name` (и автоматически генерируемым `slug`),
        - второй и последующие категории должны получать уникальный `slug` (например, `electronics`, `electronics-1`, `electronics-2` и т.д.).
        """
        
        category1 = Category.objects.create(name='Electronics 1')
        assert category1.slug == 'electronics-1'
        
        category2 = Category.objects.create(name='Electronics 2')
        assert category2.slug == 'electronics-2'
        
        category3 = Category.objects.create(name='Electronics 3')
        assert category3.slug == 'electronics-3'
        
        
        assert category1.slug != category2.slug
        assert category2.slug != category3.slug
        assert category1.slug != category3.slug
        
        
    
    def test_unique_slug_constraint(self):
        """
        Задача:
        - Проверить, что при создании категории с уже существующим значением `slug` 
        должно генерироваться исключение уникальности.
        """
        category1 = Category.objects.create(name='Electronics')
        assert category1.slug == 'electronics'
        
        with pytest.raises(IntegrityError):
            Category.objects.create(name='Electronics', slug='electronics')

    def test_parent_category(self):
        """
        Задача:
        - Проверить, что поле `parent` работает корректно для вложенных категорий (т.е. категория может быть дочерней для другой категории).
        - Вложенная категория должна отображаться в `subcategories` родительской категории.
        """
        pass
    
    def test_category_without_parent(self):
        """
        Задача:
        - Проверить, что категория без родителя имеет `parent` равное `None`.
        """
        pass
    
    def test_str_method(self):
        """
        Задача:
        - Проверить, что метод `__str__` возвращает название категории.
        """
        pass
    
    def test_icon_field(self):
        """
        Задача:
        - Проверить, что поле `icon` может быть пустым (NULL или пустая строка).
        - Проверить, что если в поле `icon` указано значение, оно сохраняется корректно.
        """
        pass
    
    def test_category_ordering(self):
        """
        Задача:
        - Проверить, что категории сортируются сначала по полю `order`, затем по полю `name`.
        """
        pass
    
    def test_nullable_and_blank_fields(self):
        """
        Задача:
        - Проверить, что поля `icon` и `parent` могут быть пустыми (NULL или пустая строка).
        """
        pass
    
    def test_slug_auto_save(self):
        """
        Задача:
        - Проверить, что метод `save` корректно генерирует и сохраняет `slug`, если он не был указан.
        """
        pass
    
    def test_large_data_handling(self):
        """
        Задача:
        - Проверить, как модель работает с большими значениями (например, очень длинные строки в поле `name`).
        """
        pass
