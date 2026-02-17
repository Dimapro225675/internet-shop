from django import forms
from django.forms import ModelForm
from django.core.exceptions import ValidationError
from .models import Category, Product


class BaseForm:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_styles()


class CategoryForm(BaseForm, ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description', 'is_active']
        labels = {
            'name': 'Название категории',
            'description': 'Описание',
            'is_active': 'Активна'
        }
        help_texts = {
            'name': 'Макс. 200 символов',
            'description': 'Необязательное поле'
        }

    def apply_styles(self):
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите название категории',
            'maxlength': 200,
            'required': True
        })
        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Краткое описание категории...'
        })
        self.fields['is_active'].widget.attrs.update({
            'class': 'form-check-input'
        })

    def clean_name(self):
        name = self.cleaned_data['name']
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Категория с таким названием уже существует')
        return name.strip()

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        if name and not self.instance.slug:
            from django.utils.text import slugify
            cleaned_data['slug'] = slugify(name)[:200]
        return cleaned_data


class ProductForm(BaseForm, ModelForm):

    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'stock', 'is_active', 'image']
        labels = {
            'name': 'Название товара',
            'category': 'Категория',
            'description': 'Описание',
            'price': 'Цена (руб.)',
            'stock': 'Количество на складе',
            'is_active': 'Доступен для продажи',
            'image': 'Изображение'
        }
        help_texts = {
            'price': 'Формат: 999.99',
            'stock': 'Минимальное значение: 0',
            'image': 'Рекомендуемый размер: 800x800px, JPG/PNG'
        }

    def apply_styles(self):
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Название товара',
            'maxlength': 255,
            'required': True
        })

        self.fields['category'].widget.attrs.update({
            'class': 'form-select',
            'required': True
        })

        self.fields['description'].widget.attrs.update({
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Подробное описание товара...'
        })

        self.fields['price'].widget.attrs.update({
            'class': 'form-control',
            'type': 'number',
            'step': '0.01',
            'min': '0.01',
            'placeholder': '0.00',
            'required': True
        })

        self.fields['stock'].widget.attrs.update({
            'class': 'form-control',
            'type': 'number',
            'min': '0',
            'placeholder': '0',
            'required': True
        })

        self.fields['is_active'].widget.attrs.update({
            'class': 'form-check-input'
        })

        self.fields['image'].widget.attrs.update({
            'class': 'form-control',
            'accept': 'image/*'
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        if self.instance.pk:
            self.fields['category'].queryset = self.fields['category'].queryset | Category.objects.filter(
                pk=self.instance.category.pk)

    def clean_name(self):
        name = self.cleaned_data['name']
        if len(name) < 2:
            raise ValidationError('Название должно содержать минимум 2 символа')
        return name.strip()

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise ValidationError('Цена должна быть больше 0')
        return price

    def clean_stock(self):
        stock = self.cleaned_data['stock']
        if stock < 0:
            raise ValidationError('Количество не может быть отрицательным')
        return stock

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.size > 5 * 1024 * 1024:
                raise ValidationError('Размер изображения не должен превышать 5MB')
            if not image.content_type.startswith('image/'):
                raise ValidationError('Файл должен быть изображением')
        return image

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        if name and not self.instance.slug:
            from django.utils.text import slugify
            cleaned_data['slug'] = slugify(name)[:255]
        return cleaned_data

class ProductSearchForm(forms.Form):
    query = forms.CharField(
        max_length=255,
        required=False,
        label='Поиск по названию или описанию',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название или описание...'
        })
    )


class CategoryBulkDeleteForm(forms.Form):
    category_ids = forms.ModelMultipleChoiceField(
        queryset=Category.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
