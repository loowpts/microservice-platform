import json
import pytest
from decimal import Decimal
from django.test import Client
from unittest.mock import patch
from apps.reviews.models import Review
from apps.products.models import Product, STATUS_CHOICES
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.views
class TestReviewListView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            title='Test Product',
            description='Test description',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

    @patch('apps.reviews.views.get_users_batch')
    def test_list_reviews_success(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'user1@example.com', 'avatar_url': 'https://avatar1.com'},
            {'id': 3, 'email': 'user3@example.com', 'avatar_url': 'https://avatar3.com'}
        ]

        Review.objects.create(
            product=self.product,
            author_id=1,
            rating=5,
            comment='Great product!'
        )

        Review.objects.create(
            product=self.product,
            author_id=3,
            rating=4,
            comment='Good product',
            pros='Quality',
            cons='Price'
        )

        response = self.client.get(f'/api/products/{self.product.slug}/reviews/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 2
        assert len(data['data']) == 2
        assert data['average_rating'] == 4.5

    def test_list_reviews_empty(self):

        response = self.client.get(f'/api/products/{self.product.slug}/reviews/')
        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
        assert data['average_rating'] is None

    @patch('apps.reviews.views.get_users_batch')
    def test_list_reviews_with_author_details(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'user@example.com', 'avatar_url': 'https://avatar.com'}
        ]

        Review.objects.create(
            product=self.product,
            author_id=1,
            rating=5,
            comment='Great product'
        )

        response = self.client.get(f'/api/products/{self.product.slug}/reviews/')
        data = response.json()

        assert response.status_code == 200
        review_data = data['data'][0]
        assert review_data['author'] is not None
        assert review_data['author']['id'] == 1
        assert review_data['author']['email'] == 'user@example.com'

    def test_list_reviews_product_not_found(self):

        response = self.client.get('/api/products/nonexistent-product/reviews/')

        assert response.status_code == 404

    @patch('apps.reviews.views.get_users_batch')
    def test_list_reviews_response_structure(self, mock_get_users_batch):

        mock_get_users_batch.return_value = [
            {'id': 1, 'email': 'user@example.com', 'avatar_url': 'https://avatar.com'}
        ]

        Review.objects.create(
            product=self.product,
            author_id=1,
            rating=5,
            comment='Test review',
            pros='Good quality',
            cons='Expensive'
        )

        response = self.client.get(f'/api/products/{self.product.slug}/reviews/')
        data = response.json()

        assert response.status_code == 200
        assert 'success' in data
        assert 'product' in data
        assert 'count' in data
        assert 'average_rating' in data
        assert 'data' in data

        review = data['data'][0]
        assert 'id' in review
        assert 'rating' in review
        assert 'comment' in review
        assert 'pros' in review
        assert 'cons' in review
        assert 'author_id' in review
        assert 'author' in review
        assert 'created_at' in review


@pytest.mark.django_db
@pytest.mark.views
class TestReviewCreateView:

    def setup_method(self):
        self.client = Client()
        self.category = Category.objects.create(name='Electronics', slug='electronics')
        self.product = Product.objects.create(
            title='Test Product',
            description='Test description',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=2,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

    @patch('apps.reviews.views.get_user')
    def test_create_review_success(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar.com'
        }

        review_data = {
            'rating': 5,
            'comment': 'Great product!',
            'pros': 'Quality and price',
            'cons': 'None found'
        }

        response = self.client.post(
            f'/api/products/{self.product.slug}/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert data['message']
        assert Review.objects.filter(product=self.product, author_id=1).exists()

    @patch('apps.reviews.views.get_user')
    def test_create_review_with_minimal_data(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar.com'
        }

        review_data = {
            'rating': 4,
            'comment': 'Good product'
        }

        response = self.client.post(
            f'/api/products/{self.product.slug}/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 200
        assert data['success'] is True
        assert Review.objects.filter(product=self.product, author_id=1).exists()

    def test_create_review_seller_cannot_review_own_product(self):

        own_product = Product.objects.create(
            title='My Product',
            description='Test',
            price=Decimal('99.99'),
            category=self.category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        review_data = {
            'rating': 5,
            'comment': 'My own product is great!'
        }

        response = self.client.post(
            f'/api/products/{own_product.slug}/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'self_review'

    @patch('apps.reviews.views.get_user')
    def test_create_review_duplicate_not_allowed(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar.com'
        }

        Review.objects.create(
            product=self.product,
            author_id=1,
            rating=5,
            comment='First review'
        )

        review_data = {
            'rating': 4,
            'comment': 'Second review'
        }

        response = self.client.post(
            f'/api/products/{self.product.slug}/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'duplicate_review'

    def test_create_review_invalid_json(self):

        response = self.client.post(
            f'/api/products/{self.product.slug}/reviews/create/',
            data='invalid json',
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert data['code'] == 'invalid_json'

    def test_create_review_invalid_data(self):

        review_data = {
            'rating': 10,
            'comment': ''
        }

        response = self.client.post(
            f'/api/products/{self.product.slug}/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 400
        assert data['success'] is False
        assert 'error' in data

    def test_create_review_product_not_found(self):

        review_data = {
            'rating': 5,
            'comment': 'Great!'
        }

        response = self.client.post(
            '/api/products/nonexistent-product/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        assert response.status_code == 404

    @patch('apps.reviews.views.get_user')
    def test_create_review_response_structure(self, mock_get_user):

        mock_get_user.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'avatar_url': 'https://avatar.com'
        }

        review_data = {
            'rating': 5,
            'comment': 'Test review',
            'pros': 'Quality',
            'cons': 'Price'
        }

        response = self.client.post(
            f'/api/products/{self.product.slug}/reviews/create/',
            data=json.dumps(review_data),
            content_type='application/json'
        )

        data = response.json()

        assert response.status_code == 200
        assert 'success' in data
        assert 'message' in data
        assert 'data' in data

        review = data['data']
        assert 'id' in review
        assert 'rating' in review
        assert 'comment' in review
        assert 'pros' in review
        assert 'cons' in review
        assert 'author_id' in review
        assert 'author' in review
        assert 'product' in review
        assert 'created_at' in review
