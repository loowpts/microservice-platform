import pytest
import time
from decimal import Decimal
from django.db import transaction, IntegrityError
from apps.reviews.models import Review
from apps.products.models import Product
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestReviewModel:

    def test_create_review_with_valid_data(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        review = Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='Great product!'
        )

        assert review.id is not None
        assert review.product == product
        assert review.author_id == 2
        assert review.rating == 5
        assert review.comment == 'Great product!'
        assert review.created_at is not None

    def test_review_with_pros_and_cons(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        review = Review.objects.create(
            product=product,
            author_id=2,
            rating=4,
            comment='Good product overall',
            pros='Great quality, fast delivery',
            cons='A bit expensive'
        )

        assert review.pros == 'Great quality, fast delivery'
        assert review.cons == 'A bit expensive'

    def test_review_unique_together_constraint(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='First review'
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(
                    product=product,
                    author_id=2,
                    rating=3,
                    comment='Second review'
                )

    def test_review_ordering_by_created_at_desc(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        review1 = Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='First review'
        )
        time.sleep(0.01)

        review2 = Review.objects.create(
            product=product,
            author_id=3,
            rating=4,
            comment='Second review'
        )
        time.sleep(0.01)

        review3 = Review.objects.create(
            product=product,
            author_id=4,
            rating=3,
            comment='Third review'
        )

        reviews = list(Review.objects.all())

        assert reviews[0] == review3
        assert reviews[1] == review2
        assert reviews[2] == review1

    def test_cascade_delete_reviews_when_product_deleted(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='Review 1'
        )

        Review.objects.create(
            product=product,
            author_id=3,
            rating=4,
            comment='Review 2'
        )

        product.delete()

        assert Review.objects.count() == 0

    def test_review_str_representation(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        review = Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='Great!'
        )

        assert '2' in str(review)
        assert 'Test Product' in str(review)

    def test_review_product_relationship(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        review = Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='Great!'
        )

        assert review.product == product
        assert review in product.reviews.all()
        assert hasattr(product, 'reviews')
        assert product.reviews.count() == 1

    def test_review_rating_choices(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        for rating in range(1, 6):
            review = Review.objects.create(
                product=product,
                author_id=rating + 1,
                rating=rating,
                comment=f'Review with rating {rating}'
            )
            assert review.rating == rating

        assert Review.objects.count() == 5

    def test_multiple_reviews_from_different_authors(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        Review.objects.create(
            product=product,
            author_id=2,
            rating=5,
            comment='Review from user 2'
        )

        Review.objects.create(
            product=product,
            author_id=3,
            rating=4,
            comment='Review from user 3'
        )

        Review.objects.create(
            product=product,
            author_id=4,
            rating=3,
            comment='Review from user 4'
        )

        assert product.reviews.count() == 3
        author_ids = [review.author_id for review in product.reviews.all()]
        assert 2 in author_ids
        assert 3 in author_ids
        assert 4 in author_ids

    def test_review_default_rating(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        review = Review.objects.create(
            product=product,
            author_id=2,
            comment='Review without explicit rating'
        )

        assert review.rating == 1
