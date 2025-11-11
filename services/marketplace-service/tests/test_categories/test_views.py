import pytest
from django.test import Client
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.views
class TestCategoryListView:

    def setup_method(self):
        self.client = Client()

    def test_list_categories_success(self):
        Category.objects.create(name='Electronics', slug='electronics')
        Category.objects.create(name='Books', slug='books')

        response = self.client.get('/api/categories/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert 'data' in data
        assert isinstance(data['data'], list)
        assert data['count'] == 2

    def test_list_categories_empty(self):
        Category.objects.all().delete()

        response = self.client.get('/api/categories/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data'] == []
        assert data['count'] == 0

    def test_list_categories_with_subcategories_count(self):
        parent = Category.objects.create(name='Parent', slug='parent')
        Category.objects.create(name='Child1', slug='child1', parent=parent)
        Category.objects.create(name='Child2', slug='child2', parent=parent)

        response = self.client.get('/api/categories/')
        data = response.json()

        parent_data = next(cat for cat in data['data'] if cat['slug'] == 'parent')
        assert parent_data['subcategories_count'] == 2

    def test_list_categories_ordering(self):
        
        Category.objects.create(name='C Category', order=1)
        Category.objects.create(name='A Category', order=0)
        Category.objects.create(name='B Category', order=0)

        response = self.client.get('/api/categories/')
        data = response.json()

        names = [cat['name'] for cat in data['data']]
        assert names[0] == 'A Category'
        assert names[1] == 'B Category'
        assert names[2] == 'C Category'

    def test_list_categories_response_structure(self):
        category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            icon='test-icon'
        )

        response = self.client.get('/api/categories/')
        data = response.json()

        cat_data = data['data'][0]
        assert 'id' in cat_data
        assert 'name' in cat_data
        assert 'slug' in cat_data
        assert 'icon' in cat_data
        assert 'parent_id' in cat_data
        assert 'subcategories_count' in cat_data
        assert cat_data['name'] == 'Test Category'
        assert cat_data['slug'] == 'test-category'
        assert cat_data['icon'] == 'test-icon'


@pytest.mark.django_db
@pytest.mark.views
class TestCategoryDetailView:

    def setup_method(self):
        self.client = Client()

    def test_retrieve_category_success(self):

        category = Category.objects.create(name='Electronics', slug='electronics')

        response = self.client.get(f'/api/categories/{category.slug}/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert 'data' in data
        assert data['data']['name'] == 'Electronics'
        assert data['data']['slug'] == 'electronics'

    def test_retrieve_category_not_found(self):

        response = self.client.get('/api/categories/nonexistent-category/')

        assert response.status_code == 404

    def test_retrieve_category_with_subcategories(self):

        parent = Category.objects.create(name='Parent', slug='parent')
        child1 = Category.objects.create(name='Child1', slug='child1', parent=parent, order=1)
        child2 = Category.objects.create(name='Child2', slug='child2', parent=parent, order=0)

        response = self.client.get(f'/api/categories/{parent.slug}/')
        data = response.json()

        assert response.status_code == 200
        assert data['data']['subcategories_count'] == 2
        assert isinstance(data['data']['subcategories_data'], list)
        assert len(data['data']['subcategories_data']) == 2

        subcats = data['data']['subcategories_data']
        assert subcats[0]['slug'] == 'child2'
        assert subcats[1]['slug'] == 'child1'

    def test_retrieve_category_with_parent(self):
        
        parent = Category.objects.create(name='Parent', slug='parent')
        child = Category.objects.create(name='Child', slug='child', parent=parent)

        response = self.client.get(f'/api/categories/{child.slug}/')
        data = response.json()

        assert response.status_code == 200
        assert data['data']['parent'] is not None
        assert data['data']['parent']['name'] == 'Parent'
        assert data['data']['parent']['slug'] == 'parent'
        assert 'id' in data['data']['parent']

    def test_retrieve_category_without_parent(self):

        category = Category.objects.create(name='Category', slug='category')

        response = self.client.get(f'/api/categories/{category.slug}/')
        data = response.json()

        assert response.status_code == 200
        assert data['data']['parent'] is None

    def test_retrieve_category_response_structure(self):

        category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            icon='test-icon'
        )

        response = self.client.get(f'/api/categories/{category.slug}/')
        data = response.json()

        cat_data = data['data']
        assert 'id' in cat_data
        assert 'name' in cat_data
        assert 'slug' in cat_data
        assert 'icon' in cat_data
        assert 'parent' in cat_data
        assert 'subcategories_count' in cat_data
        assert 'subcategories_data' in cat_data

    def test_retrieve_category_empty_subcategories(self):

        category = Category.objects.create(name='Category', slug='category')

        response = self.client.get(f'/api/categories/{category.slug}/')
        data = response.json()

        assert response.status_code == 200
        assert data['data']['subcategories_count'] == 0
        assert data['data']['subcategories_data'] == []
