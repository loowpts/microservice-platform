import pytest
from apps.categories.models import Category


@pytest.mark.django_db
class TestCategoryModel:
    
    def test_create_category_basic(self):
        """
        Проверяемые аспекты:
        - Категория создается с именем
        - Slug генерируется автоматически
        - order по умолчанию = 0
        - parent по умолчанию = None
        """
        
        category = Category.objects.create(
            name='Test Name'
        )
        
        assert category.slug == 'test-name'
        assert category.order == 0
        assert category.parent is None
    
    def test_category_slug_generation_cyrillic(self):
        """
        Проверяемые аспекты:
        - name="Электроника" → slug="elektronika"
        - Транслитерация работает корректно
        """
        
        category = Category.objects.create(
            name='Электроника'
        )
        
        assert category.slug == 'elektronika'    
    
    def test_category_slug_underscore_replacement(self):
        """
        Проверяемые аспекты:
        - name с подчеркиванием должен давать slug с дефисом
        - "Test_Category" → "test-category"
        """
        category = Category.objects.create(
            name='Test_Category'
        )

        assert '_' not in category.slug
        assert '-' in category.slug
        assert category.slug == 'test-category'
    
    def test_category_parent_child_relationship(self):
        """
        Проверяемые аспекты:
        - Создать родительскую категорию
        - Создать дочернюю с parent=родитель
        - Проверить parent.subcategories.count() == 1
        - Проверить child.parent == parent
        """
        parent = Category.objects.create(
            name='Parent Category'
        )

        child = Category.objects.create(
            name='Child Category',
            parent=parent
        )

        assert child.parent == parent
        assert parent.subcategories.count() == 1
        assert child in parent.subcategories.all()
        assert hasattr(parent, 'subcategories')
    
    def test_category_ordering(self):
        """
        Проверяемые аспекты:
        - Создать 3 категории с разными order (2, 0, 1)
        - Запросить Category.objects.all()
        - Проверить порядок: 0, 1, 2
        """
        cat1 = Category.objects.create(name='Category B', order=2)
        cat2 = Category.objects.create(name='Category A', order=0)
        cat3 = Category.objects.create(name='Category C', order=1)

        categories = list(Category.objects.all())

        assert categories[0] == cat2  # order=0
        assert categories[1] == cat3  # order=1
        assert categories[2] == cat1  # order=2
        assert categories[0].order < categories[1].order < categories[2].order
    
    def test_category_cascade_delete(self):
        """
        Проверяемые аспекты:
        - Создать родителя и ребенка
        - Удалить родителя
        - Проверить что ребенок тоже удален
        """
        parent = Category.objects.create(name='Parent')
        child = Category.objects.create(name='Child', parent=parent)

        parent_id = parent.id
        child_id = child.id

        parent.delete()

        assert not Category.objects.filter(id=parent_id).exists()
        assert not Category.objects.filter(id=child_id).exists()
        assert Category.objects.count() == 0
    
    def test_category_str_method(self):
        """
        Проверяемые аспекты:
        - str(category) возвращает category.name
        """
        category = Category.objects.create(name='Test Category')

        assert str(category) == 'Test Category'
        assert str(category) == category.name
