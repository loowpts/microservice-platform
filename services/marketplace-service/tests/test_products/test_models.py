import pytest
import time
from decimal import Decimal
from django.db import transaction, IntegrityError
from apps.products.models import Product, ProductImage, CONDITION_CHOICES, STATUS_CHOICES
from apps.categories.models import Category


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestProductModel:

    def test_create_product_with_valid_data(self):

        category = Category.objects.create(name='Electronics')

        product = Product.objects.create(
            title='iPhone 15',
            description='Latest iPhone model',
            price=Decimal('999.99'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        assert product.id is not None
        assert product.title == 'iPhone 15'
        assert product.slug == 'iphone-15'
        assert product.price == Decimal('999.99')
        assert product.category == category
        assert product.seller_id == 1
        assert product.city == 'Moscow'
        assert product.condition == CONDITION_CHOICES.NEW
        assert product.status == STATUS_CHOICES.DRAFT
        assert product.quantity == 1
        assert product.views_count == 0
        assert product.created_at is not None
        assert product.updated_at is not None

    def test_slug_auto_generation_from_title(self):

        category = Category.objects.create(name='Electronics')

        product = Product.objects.create(
            title='MacBook Pro 16',
            description='Professional laptop',
            price=Decimal('2499.99'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        assert product.slug == 'macbook-pro-16'
        assert product.slug.islower()
        assert ' ' not in product.slug

    def test_product_title_must_be_unique(self):

        category = Category.objects.create(name='Electronics')

        Product.objects.create(
            title='Unique Product',
            description='First product',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Product.objects.create(
                    title='Unique Product',
                    description='Second product',
                    price=Decimal('200.00'),
                    category=category,
                    seller_id=2,
                    city='Moscow'
                )

    def test_slug_uniqueness_with_duplicates(self):

        category = Category.objects.create(name='Electronics')

        product1 = Product.objects.create(
            title='Test Product One',
            description='First',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        product2 = Product.objects.create(
            title='Test Product Two',
            description='Second',
            price=Decimal('200.00'),
            category=category,
            seller_id=1,
            city='Moscow',
            slug=''
        )

        assert product1.slug == 'test-product-one'
        assert product2.slug == 'test-product-two'

    def test_product_ordering_by_created_at_desc(self):

        category = Category.objects.create(name='Electronics')

        product1 = Product.objects.create(
            title='Product 1',
            description='First',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )
        time.sleep(0.01)

        product2 = Product.objects.create(
            title='Product 2',
            description='Second',
            price=Decimal('200.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )
        time.sleep(0.01)

        product3 = Product.objects.create(
            title='Product 3',
            description='Third',
            price=Decimal('300.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        products = list(Product.objects.all())

        assert products[0] == product3
        assert products[1] == product2
        assert products[2] == product1

    def test_cascade_delete_products_when_category_deleted(self):

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

        category.delete()

        assert not Category.objects.filter(id=category.id).exists()
        assert Product.objects.count() == 0

    def test_product_str_representation(self):

        category = Category.objects.create(name='Electronics')

        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        assert str(product) == 'Test Product'
        assert str(product) == product.title

    def test_product_with_old_price(self):

        category = Category.objects.create(name='Electronics')

        product = Product.objects.create(
            title='Discounted Product',
            description='Product on sale',
            price=Decimal('79.99'),
            old_price=Decimal('99.99'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        assert product.old_price == Decimal('99.99')
        assert product.price == Decimal('79.99')
        assert product.old_price > product.price

    def test_product_condition_choices(self):

        category = Category.objects.create(name='Electronics')

        new_product = Product.objects.create(
            title='New Product',
            description='Brand new',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        used_product = Product.objects.create(
            title='Used Product',
            description='Pre-owned',
            price=Decimal('50.00'),
            category=category,
            seller_id=1,
            condition=CONDITION_CHOICES.USED,
            city='Moscow'
        )

        assert new_product.condition == CONDITION_CHOICES.NEW
        assert used_product.condition == CONDITION_CHOICES.USED

    def test_product_status_choices(self):

        category = Category.objects.create(name='Electronics')

        draft_product = Product.objects.create(
            title='Draft Product',
            description='Not published',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        active_product = Product.objects.create(
            title='Active Product',
            description='Available',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            status=STATUS_CHOICES.ACTIVE,
            city='Moscow'
        )

        assert draft_product.status == STATUS_CHOICES.DRAFT
        assert active_product.status == STATUS_CHOICES.ACTIVE

    def test_product_category_relationship(self):

        category = Category.objects.create(name='Electronics')

        product = Product.objects.create(
            title='Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        assert product.category == category
        assert product in category.products.all()
        assert hasattr(category, 'products')


@pytest.mark.django_db
@pytest.mark.unit
@pytest.mark.models
class TestProductImageModel:

    def test_create_product_image(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        image = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image.jpg'
        )

        assert image.id is not None
        assert image.product == product
        assert image.image_url == 'https://example.com/image.jpg'
        assert image.order == 0
        assert image.is_primary is False

    def test_product_image_relationship(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        image1 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image1.jpg',
            order=0
        )

        image2 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image2.jpg',
            order=1
        )

        assert product.additional_images.count() == 2
        assert image1 in product.additional_images.all()
        assert image2 in product.additional_images.all()

    def test_product_image_cascade_delete(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image1.jpg'
        )

        ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image2.jpg'
        )

        product.delete()

        assert ProductImage.objects.count() == 0

    def test_product_image_ordering(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        image3 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image3.jpg',
            order=2
        )

        image1 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image1.jpg',
            order=0
        )

        image2 = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image2.jpg',
            order=1
        )

        images = list(product.additional_images.all())

        assert images[0] == image1
        assert images[1] == image2
        assert images[2] == image3

    def test_product_image_str_representation(self):

        category = Category.objects.create(name='Electronics')
        product = Product.objects.create(
            title='Test Product',
            description='Test',
            price=Decimal('100.00'),
            category=category,
            seller_id=1,
            city='Moscow'
        )

        image = ProductImage.objects.create(
            product=product,
            image_url='https://example.com/image.jpg'
        )

        assert 'Test Product' in str(image)
        assert str(image) == 'Image for Test Product'
