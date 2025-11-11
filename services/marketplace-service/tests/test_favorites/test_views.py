import pytest
from decimal import Decimal
from django.test import Client
from unittest.mock import patch
from apps.favorites.models import Favorite
from apps.products.models import Product, STATUS_CHOICES
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.views
class TestFavoriteListView:

    def setup_method(self):

        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')

    @patch('apps.favorites.views.get_users_batch')
    def test_list_favorites_success(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 2, 'username': 'seller', 'email': 'seller@example.com'}
        ]

        product1 = Product.objects.create(
            title='Product 1',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        product2 = Product.objects.create(
            title='Product 2',
            description='Test',
            price=Decimal('149.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Favorite.objects.create(user_id=1, product=product1)
        Favorite.objects.create(user_id=1, product=product2)

        Favorite.objects.create(user_id=3, product=product1)

        response = self.client.get('/api/favorites/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert data['count'] == 2
        assert len(data['data']) == 2

    def test_list_favorites_empty(self):

        response = self.client.get('/api/favorites/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['data'] == []
        assert data['count'] == 0

    @patch('apps.favorites.views.get_users_batch')
    def test_list_favorites_with_product_details(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 2, 'username': 'seller', 'email': 'seller@example.com'}
        ]

        product = Product.objects.create(
            title='Favorite Product',
            description='Test product',
            price=Decimal('199.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        Favorite.objects.create(user_id=1, product=product)

        response = self.client.get('/api/favorites/')
        data = response.json()

        assert response.status_code == 200
        product_data = data['data'][0]['product']
        assert product_data['title'] == 'Favorite Product'
        assert product_data['slug'] == 'favorite-product'
        assert float(product_data['price']) == 199.99


@pytest.mark.django_db
@pytest.mark.views
class TestFavoriteToggleView:

    def setup_method(self):
        
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

    def test_add_to_favorites_success(self):

        response = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert 'Товар добавлен в избранное' in data['message']
        assert Favorite.objects.filter(user_id=1, product=self.product).exists()

    def test_remove_from_favorites_success(self):

        Favorite.objects.create(user_id=1, product=self.product)

        response = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert 'Товар удален из избранного' in data['message']
        assert not Favorite.objects.filter(user_id=1, product=self.product).exists()

    def test_toggle_favorite_multiple_times(self):

        response1 = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        assert response1.status_code == 200
        assert Favorite.objects.filter(user_id=1, product=self.product).exists()

        response2 = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        assert response2.status_code == 200
        assert not Favorite.objects.filter(user_id=1, product=self.product).exists()

        response3 = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        assert response3.status_code == 200
        assert Favorite.objects.filter(user_id=1, product=self.product).exists()

    def test_toggle_favorite_product_not_found(self):

        response = self.client.post('/api/products/nonexistent-product/favorite/')

        assert response.status_code == 404

    def test_different_users_can_favorite_same_product(self):

        Favorite.objects.create(user_id=1, product=self.product)

        Favorite.objects.create(user_id=2, product=self.product)

        assert Favorite.objects.filter(product=self.product).count() == 2
        assert Favorite.objects.filter(user_id=1, product=self.product).exists()
        assert Favorite.objects.filter(user_id=2, product=self.product).exists()

    def test_user_can_favorite_multiple_products(self):

        product2 = Product.objects.create(
            title='Product 2',
            description='Test',
            price=Decimal('149.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        response1 = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        assert response1.status_code == 200

        response2 = self.client.post(f'/api/products/{product2.slug}/favorite/')
        assert response2.status_code == 200

        assert Favorite.objects.filter(user_id=1).count() == 2

    def test_favorite_count_in_response(self):

        response = self.client.post(f'/api/products/{self.product.slug}/favorite/')
        data = response.json()

        assert 'is_favorited' in data or 'Товар добавлен в избранное' in data['message']
        assert Favorite.objects.filter(user_id=1, product=self.product).exists()
