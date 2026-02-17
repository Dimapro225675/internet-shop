import pytest
import django
from django.core.exceptions import ValidationError
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from catalog.models import Category, Product

@pytest.fixture
def category():
    return Category.objects.create(name="Тестовая категория")

@pytest.mark.django_db
class TestCategoryModel:

    def test_slug_not_changed_if_exists(self):
        category = Category.objects.create(name="Тест", slug="test-slug")
        original_slug = category.slug
        category.name = "Измененное название"
        category.save()
        assert category.slug == original_slug

    def test_slug_truncation(self):
        long_name = "a" * 210
        category = Category(name=long_name)
        category.save()
        assert len(category.slug) <= 200

    def test_unique_slug_validation(self):
        Category.objects.create(name="Тест", slug="test")
        category2 = Category(name="Тест 2", slug="test")
        with pytest.raises(ValidationError):
            category2.full_clean()

    def test_can_delete_no_products(self, category):
        assert category.can_delete() is True

    def test_can_delete_with_products(self, category):
        Product.objects.create(name="Товар", category=category, price=100)
        assert category.can_delete() is False

@pytest.mark.django_db
class TestProductModel:

    def test_slug_not_changed_if_exists(self):
        category = Category.objects.create(name="Категория")
        product = Product.objects.create(
            name="Тест",
            category=category,
            price=100,
            slug="test-slug"
        )
        original_slug = product.slug
        product.name = "Измененное название"
        product.save()
        assert product.slug == original_slug

    def test_slug_truncation(self):
        category = Category.objects.create(name="Категория")
        long_name = "a" * 260
        product = Product(name=long_name, category=category, price=100)
        product.save()
        assert len(product.slug) <= 255

    def test_unique_slug_validation(self):
        category = Category.objects.create(name="Категория")
        Product.objects.create(name="Тест", category=category, price=100, slug="test")
        product2 = Product(name="Тест 2", category=category, price=200, slug="test")
        with pytest.raises(ValidationError):
            product2.full_clean()

    def test_image_upload_path(self):
        category = Category.objects.create(name="Категория")
        product = Product(
            name="Товар с картинкой",
            category=category,
            price=100,
            slug="test-product"
        )
        product.save()

        image = Image.new('RGB', (100, 100), color='red')
        img_buffer = BytesIO()
        image.save(img_buffer, format='JPEG')
        img_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test.jpg',
            img_buffer.read(),
            content_type='image/jpeg'
        )

        product.image = uploaded_file
        product.save()
        assert product.image.name.startswith('products/test-product/')

    def test_protect_category_deletion(self, category):
        product = Product.objects.create(name="Товар", category=category, price=100)
        with pytest.raises(Exception):
            category.delete()
