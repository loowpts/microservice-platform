import pytest
import time
from decimal import Decimal
from django.db import transaction, IntegrityError
from apps.favorites.models import Favorite
from apps.products.models import Product
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestFavoriteModel:

    def test_create_favorite_with_valid_data(self):
        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        favorite = Favorite.objects.create(
            user_id=2,
            product=product
        )

        assert favorite.id is not None
        assert favorite.user_id == 2
        assert favorite.product == product
        assert favorite.created_at is not None

    def test_favorite_unique_together_constraint(self):
        
        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Favorite.objects.create(
            user_id=2,
            product=product
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Favorite.objects.create(
                    user_id=2,
                    product=product
                )

    def test_favorite_ordering_by_created_at_desc(self):
        
        category = Category.objects.create(name='Electronics')

        product1 = Product.objects.create(
            title='Product 1',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        product2 = Product.objects.create(
            title='Product 2',
            description='Test',
            price=Decimal('200.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        product3 = Product.objects.create(
            title='Product 3',
            description='Test',
            price=Decimal('300.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        favorite1 = Favorite.objects.create(user_id=2, product=product1)
        time.sleep(0.01)
        favorite2 = Favorite.objects.create(user_id=2, product=product2)
        time.sleep(0.01)
        favorite3 = Favorite.objects.create(user_id=2, product=product3)

        favorites = list(Favorite.objects.all())

        assert favorites[0] == favorite3
        assert favorites[1] == favorite2
        assert favorites[2] == favorite1

    def test_cascade_delete_favorites_when_product_deleted(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Favorite.objects.create(user_id=2, product=product)
        Favorite.objects.create(user_id=3, product=product)
        Favorite.objects.create(user_id=4, product=product)

        product.delete()

        assert Favorite.objects.count() == 0

    def test_favorite_str_representation(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        favorite = Favorite.objects.create(
            user_id=2,
            product=product
        )

        assert '2' in str(favorite)
        assert 'Test Product' in str(favorite)

    def test_favorite_product_relationship(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        favorite = Favorite.objects.create(
            user_id=2,
            product=product
        )

        assert favorite.product == product
        assert favorite in product.favorites.all()
        assert hasattr(product, 'favorites')
        assert product.favorites.count() == 1

    def test_multiple_users_can_favorite_same_product(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Favorite.objects.create(user_id=2, product=product)
        Favorite.objects.create(user_id=3, product=product)
        Favorite.objects.create(user_id=4, product=product)

        assert product.favorites.count() == 3
        user_ids = [fav.user_id for fav in product.favorites.all()]
        assert 2 in user_ids
        assert 3 in user_ids
        assert 4 in user_ids

    def test_one_user_can_favorite_multiple_products(self):

        category = Category.objects.create(name='Electronics')

        product1 = Product.objects.create(
            title='Product 1',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        product2 = Product.objects.create(
            title='Product 2',
            description='Test',
            price=Decimal('200.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        product3 = Product.objects.create(
            title='Product 3',
            description='Test',
            price=Decimal('300.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Favorite.objects.create(user_id=2, product=product1)
        Favorite.objects.create(user_id=2, product=product2)
        Favorite.objects.create(user_id=2, product=product3)

        user_favorites = Favorite.objects.filter(user_id=2)
        assert user_favorites.count() == 3

        product_titles = [fav.product.title for fav in user_favorites]
        assert 'Product 1' in product_titles
        assert 'Product 2' in product_titles
        assert 'Product 3' in product_titles

    def test_removing_favorite(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        favorite = Favorite.objects.create(user_id=2, product=product)

        assert Favorite.objects.count() == 1

        favorite.delete()

        assert Favorite.objects.count() == 0
        assert not Favorite.objects.filter(user_id=2, product=product).exists()

    def test_get_user_favorites(self):

        category = Category.objects.create(name='Electronics')

        product1 = Product.objects.create(
            title='Product 1',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        product2 = Product.objects.create(
            title='Product 2',
            description='Test',
            price=Decimal('200.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Favorite.objects.create(user_id=2, product=product1)
        Favorite.objects.create(user_id=2, product=product2)

        Favorite.objects.create(user_id=3, product=product1)

        user2_favorites = Favorite.objects.filter(user_id=2)
        user3_favorites = Favorite.objects.filter(user_id=3)

        assert user2_favorites.count() == 2
        assert user3_favorites.count() == 1

        assert product1 in [fav.product for fav in user2_favorites]
        assert product2 in [fav.product for fav in user2_favorites]
