import pytest
from decimal import Decimal
from django.test import Client
from unittest.mock import patch
from apps.products.models import Product, STATUS_CHOICES, CONDITION_CHOICES
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.views
class TestProductSearchView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.search.views.get_users_batch')
    def test_search_products_success(self, mock_get_users_batch):
 
        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='iPhone 15 Pro',
            description='Latest Apple smartphone',
            price=Decimal('999.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Samsung Galaxy',
            description='Android smartphone',
            price=Decimal('799.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=iPhone')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 1
        assert data['query'] == 'iPhone'
        assert 'iPhone' in data['data'][0]['title']

    def test_search_products_missing_query(self):

        response = self.client.get('/api/search/products/')
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'missing_query'

    def test_search_products_query_too_short(self):

        response = self.client.get('/api/search/products/?q=a')
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'query_too_short'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_no_results(self, mock_get_users_batch):

        mock_get_users_batch.return_value = []

        response = self.client.get('/api/search/products/?q=nonexistent')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
        assert data['query'] == 'nonexistent'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_by_title_and_description(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Laptop',
            description='Professional gaming laptop with RTX',
            price=Decimal('1499.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Gaming Mouse',
            description='Wireless mouse for gaming',
            price=Decimal('59.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=gaming')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 2

    @patch('apps.search.views.get_users_batch')
    def test_search_products_with_category_filter(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        books_category = Category.objects.create(name='Books', slug='books')

        Product.objects.create(
            title='Python Programming Book',
            description='Learn Python',
            price=Decimal('29.99'),
            category=books_category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Python Course',
            description='Online Python course',
            price=Decimal('49.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=Python&category=books')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['category']['slug'] == 'books'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_with_city_filter(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Product Moscow',
            description='Test product',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Product SPB',
            description='Test product',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='St Petersburg'
        )

        response = self.client.get('/api/search/products/?q=Product&city=Moscow')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['city'] == 'Moscow'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_with_price_range(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Cheap Product',
            description='Budget option',
            price=Decimal('50.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Medium Product',
            description='Mid-range option',
            price=Decimal('100.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Expensive Product',
            description='Premium option',
            price=Decimal('200.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=Product&price_min=75&price_max=150')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['title'] == 'Medium Product'

    def test_search_products_invalid_price_min(self):

        response = self.client.get('/api/search/products/?q=Product&price_min=-10')
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'invalid_price_min'

    def test_search_products_invalid_price_max(self):

        response = self.client.get('/api/search/products/?q=Product&price_max=-10')
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'invalid_price_max'

    def test_search_products_invalid_price_range(self):

        response = self.client.get('/api/search/products/?q=Product&price_min=200&price_max=100')
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'invalid_price_range'

    def test_search_products_invalid_price_format(self):

        response = self.client.get('/api/search/products/?q=Product&price_min=abc')
        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'invalid_price_format'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_with_condition_filter(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='New Product',
            description='Brand new',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            condition=CONDITION_CHOICES.NEW,
            city='Moscow'
        )

        Product.objects.create(
            title='Used Product',
            description='Pre-owned',
            price=Decimal('49.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            condition=CONDITION_CHOICES.USED,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=Product&condition=new')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['condition'] == 'new'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_title_priority(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Gaming Laptop',
            description='Powerful laptop',
            price=Decimal('1499.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Office Laptop',
            description='Perfect for gaming and work',
            price=Decimal('999.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=gaming')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 2

        assert 'Gaming' in data['data'][0]['title']

    @patch('apps.search.views.get_users_batch')
    def test_search_products_only_active_status(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Active Product',
            description='Available',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Product.objects.create(
            title='Draft Product',
            description='Not published',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.DRAFT,
            city='Moscow'
        )

        Product.objects.create(
            title='Sold Product',
            description='Already sold',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.SOLD,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=Product')
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['status'] == 'active'

    @patch('apps.search.views.get_users_batch')
    def test_search_products_case_insensitive(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='iPhone 15',
            description='Apple smartphone',
            price=Decimal('999.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response1 = self.client.get('/api/search/products/?q=iphone')
        response2 = self.client.get('/api/search/products/?q=IPHONE')
        response3 = self.client.get('/api/search/products/?q=iPhone')

        assert response1.json()['count'] == 1
        assert response2.json()['count'] == 1
        assert response3.json()['count'] == 1

    @patch('apps.search.views.get_users_batch')
    def test_search_products_response_structure(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('99.99'),
            old_price=Decimal('149.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            condition=CONDITION_CHOICES.NEW,
            city='Moscow'
        )

        response = self.client.get('/api/search/products/?q=Test')
        data = response.json()

        assert response.status_code == 200
        assert 'success' in data
        assert 'query' in data
        assert 'count' in data
        assert 'data' in data

        product_data = data['data'][0]
        assert 'id' in product_data
        assert 'title' in product_data
        assert 'slug' in product_data
        assert 'price' in product_data
        assert 'old_price' in product_data
        assert 'category' in product_data
        assert 'condition' in product_data
        assert 'city' in product_data
        assert 'status' in product_data
        assert 'seller_id' in product_data
        assert 'seller' in product_data
        assert 'views_count' in product_data
        assert 'created_at' in product_data

    @patch('apps.search.views.get_users_batch')
    def test_search_products_with_all_filters(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'username': 'seller1', 'email': 'seller1@example.com'}
        ]

        Product.objects.create(
            title='Gaming Laptop HP',
            description='Perfect for gaming',
            price=Decimal('1200.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            condition=CONDITION_CHOICES.NEW,
            city='Moscow'
        )

        Product.objects.create(
            title='Gaming Laptop Dell',
            description='Great gaming performance',
            price=Decimal('1500.00'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            condition=CONDITION_CHOICES.NEW,
            city='St Petersburg'
        )

        response = self.client.get(
            '/api/search/products/?q=gaming&category=electronics&city=Moscow&price_min=1000&price_max=1300&condition=new'
        )
        data = response.json()

        assert response.status_code == 200
        assert data['count'] == 1
        assert data['data'][0]['title'] == 'Gaming Laptop HP'
