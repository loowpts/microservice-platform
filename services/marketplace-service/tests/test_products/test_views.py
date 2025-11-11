import json
import pytest
from decimal import Decimal
from django.test import Client
from unittest.mock import patch
from apps.products.models import Product, STATUS_CHOICES, CONDITION_CHOICES
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.views
class TestProductListView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.products.views.get_users_batch')
    def test_list_products_success(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Product 1',
            description='Test product',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/products/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert data['count'] == 1

    def test_list_products_empty(self):

        Product.objects.all().delete()

        response = self.client.get('/api/products/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data'] == []
        assert data['count'] == 0

    @patch('apps.products.views.get_users_batch')
    def test_list_products_filter_by_category(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        category2 = Category.objects.create(name='Books', slug='books')

        Product.objects.create(
            title='Phone',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Book',
            description='Test',
            price=Decimal('19.99'),
            category=category2,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/products/?category=electronics')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['title'] == 'Phone'

    @patch('apps.products.views.get_users_batch')
    def test_list_products_filter_by_city(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Product Moscow',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Product SPB',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='St Petersburg'
        )

        response = self.client.get('/api/products/?city=moscow')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['city'] == 'Moscow'

    @patch('apps.products.views.get_users_batch')
    def test_list_products_filter_by_price_range(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Cheap Product',
            description='Test',
            price=Decimal('50.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Medium Product',
            description='Test',
            price=Decimal('100.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Expensive Product',
            description='Test',
            price=Decimal('200.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/products/?price_min=75&price_max=150')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['title'] == 'Medium Product'


@pytest.mark.django_db
@pytest.mark.views
class TestProductDetailView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.products.views.get_user')
    def test_retrieve_product_success(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'username': 'seller1',
            'email': 'seller1@example.com'
        }

        product = Product.objects.create(
            title='Test Product',
            description='Test description',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        initial_views = product.views_count

        response = self.client.get(f'/api/products/{product.slug}/')
        data = response.json()

        product.refresh_from_db()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['title'] == 'Test Product'
        assert product.views_count == initial_views + 1

    def test_retrieve_product_not_found(self):

        response = self.client.get('/api/products/nonexistent-product/')

        assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.views
class TestProductCreateView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.products.views.get_user')
    def test_create_product_success(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar_test.com'
        }
        
        product_data = {
            'title': 'New Product',
            'description': 'Product description with enough characters',
            'price': 149.99,
            'category': self.category.id,
            'condition': 'new',
            'city': 'Moscow',
            'quantity': 5
        }

        response = self.client.post(
            '/api/products/create/',
            data=json.dumps(product_data),
            content_type='application/json'
        )

        data = response.json()

        if response.status_code != 201:
            print(f"Response data: {data}")

        assert response.status_code == 201
        assert data['success'] is True
        assert Product.objects.filter(title='New Product').exists()

    def test_create_product_invalid_data(self):

        product_data = {
            'title': 'Too short',
            'price': -10 
        }

        response = self.client.post(
            '/api/products/create/',
            data=product_data,
            content_type='application/json'
        )
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert not Product.objects.filter(title='Too short').exists()


@pytest.mark.django_db
@pytest.mark.views
class TestProductUpdateView:

    def setup_method(self):
        
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.products.views.get_user')
    def test_update_product_success(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar_test.com'
        }

        product = Product.objects.create(
            title='Original Title',
            description='Original description',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.DRAFT,
            city='Moscow'
        )

        update_data = {
            'title': 'Updated Title',
            'description': 'Original description',
            'price': 79.99,
            'category': self.category.id,
            'condition': 'new',
            'city': 'Moscow',
            'quantity': 1
        }

        response = self.client.patch(
            f'/api/products/{product.slug}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        data = response.json()

        product.refresh_from_db()

        assert response.status_code == 200
        assert data['success'] is True
        assert product.title == 'Updated Title'
        assert product.price == Decimal('79.99')

    def test_update_product_forbidden(self):

        product = Product.objects.create(
            title='Product',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=999,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        update_data = {'title': 'Hacked Title'}

        response = self.client.patch(
            f'/api/products/{product.slug}/update/',
            data=update_data,
            content_type='application/json'
        )
        data = response.json()

        product.refresh_from_db()

        assert response.status_code == 403
        assert data['success'] is False
        assert product.title == 'Product'


@pytest.mark.django_db
@pytest.mark.views
class TestProductDeleteView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    def test_delete_product_success(self):

        product = Product.objects.create(
            title='Product to Delete',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            city='Moscow'
        )

        response = self.client.delete(f'/api/products/{product.slug}/delete/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert not Product.objects.filter(slug=product.slug).exists()

    def test_delete_product_forbidden(self):

        product = Product.objects.create(
            title='Protected Product',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=999,
            city='Moscow'
        )

        response = self.client.delete(f'/api/products/{product.slug}/delete/')
        data = response.json()

        assert response.status_code == 403
        assert data['success'] is False
        assert Product.objects.filter(slug=product.slug).exists()


@pytest.mark.django_db
@pytest.mark.views
class TestMyProductsView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.products.views.get_users_batch')
    def test_my_products_success(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'user1', 'email': 'user1@example.com'}
        ]

        Product.objects.create(
            title='My Product 1',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            city='Moscow'
        )

        Product.objects.create(
            title='My Product 2',
            description='Test',
            price=Decimal('149.99'),
            category=self.category,
            seller_id=1,
            city='Moscow'
        )

        Product.objects.create(
            title='Other Product',
            description='Test',
            price=Decimal('199.99'),
            category=self.category,
            seller_id=2,
            city='Moscow'
        )

        response = self.client.get('/api/products/my/')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 2
        assert all(p['title'].startswith('My Product') for p in data['data'])
