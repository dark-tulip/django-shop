import sys
from PIL import Image

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.deletion import CASCADE
from django.urls import reverse
from django.utils import timezone
  
from io import BytesIO

from django.db.models.fields import files

User = get_user_model()

def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})
    

#********************* МОДЕЛИ ДЛЯ ПРИЛОЖЕНИЯ ИНТЕРНЕТ МАГАЗИНА
# 1 Category

# 2 Products we need to sell

# 3 CartProduct

# 4 Cart - basket

# 5 Order
#*********************
# 6 Customer


class MinResolutionExceptionError():
    pass


class MaxResolutionExceptionError():
    pass


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')  # Последние 5 товаров из модели ноутбук или смартфон

        products = []
        ct_models = ContentType.objects.filter(model__in=args)  # content_type_model
        for ct_model in ct_models:
            # последние 5 продуктов
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)

        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists() and with_respect_to in args:
                return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )

        return products
        

class LatestProducts:
    objects = LatestProductsManager()


class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Художественная литература': 'fictionbook__count',
        'Научная литература': 'sciencebook__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_left_sidebar(self):
        models = get_models_for_count('fictionbook', 'sciencebook')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(), count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data

class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name='Имя категории')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name


    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='Категория', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Наименование')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='Изображение')
    description = models.TextField(verbose_name='Описание', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Цена')

    def __str__(self):
        return self.title

            
    def get_model_name(self):
        return self.__class__.__name__.lower()


    def save(self, *args, **kwargs):

        # Здеь начинается обрезка фотографий при превышении макисмального размера
        image = self.image
        img = Image.open(image)
        new_img = img.convert('RGB')
        resized_new_image = new_img.resize((350, 550), Image.ANTIALIAS)
        filestream = BytesIO()

        resized_new_image.save(filestream, 'JPEG', quality=90)
        filestream.seek(0)
        name = '{}.{}'.format(*self.image.name.split('.'))

        self.image = InMemoryUploadedFile(
            filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
        )

        super().save(*args, **kwargs)


class Cartproduct(models.Model):

    user = models.ForeignKey('Customer', verbose_name='Покупатель', on_delete=models.CASCADE)
    cart = models.ForeignKey('Cart', verbose_name='Корзина', on_delete=models.CASCADE, related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)

    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Общая Цена')

    def __str__(self):
        return "Продукт: {} (для корзины)".format(self.content_object.title)

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.content_object.price
        super().save(*args, **kwargs)



class Cart(models.Model):
    
    owner = models.ForeignKey('Customer', null=True, verbose_name='Владелец', on_delete=models.CASCADE)
    products = models.ManyToManyField(Cartproduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, default=0, decimal_places=2, verbose_name='Общая цена')
    in_order = models.BooleanField(default=False)               # Статус или стадия заказа
    for_anonymous_user = models.BooleanField(default=False)     # Для незарегистрированных пользователей
    
    def __str__(self):  
        return str(self.id)


class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='Пользователь', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, null=True, verbose_name='Номер телефона', blank=True)
    address = models.CharField(max_length=255, verbose_name='Адрес', null=True, blank=True)
    orders = models.ManyToManyField('Order', verbose_name='Заказы покупателя', related_name='related_customer')

    def __str__(self):
        return "Покупатель: {} {}".format(self.user.first_name, self.user.last_name)


class FictionBook(Product):

    publisher = models.CharField(max_length=255, verbose_name='Издательство')
    binding = models.CharField(max_length=255, verbose_name='Переплет')
    size = models.CharField(max_length=255, verbose_name='Размер')
    paper = models.CharField(max_length=255, verbose_name='Бумага')

    ISBN = models.CharField(max_length=255, verbose_name='ISBN')
    edition = models.PositiveIntegerField(default=0, verbose_name='Тираж')
    language = models.CharField(max_length=255, verbose_name='Язык')
    product_code = models.CharField(max_length=255, verbose_name='Код товара')


    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class ScienceBook(Product):

    publisher = models.CharField(max_length=255, verbose_name='Издательство')
    binding = models.CharField(max_length=255, verbose_name='Переплет')
    size = models.CharField(max_length=255, verbose_name='Размер')
    paper = models.CharField(max_length=255, verbose_name='Бумага')

    ISBN = models.CharField(max_length=255, verbose_name='ISBN')
    edition = models.PositiveIntegerField(default=0, verbose_name='Тираж')
    language = models.CharField(max_length=255, verbose_name='Язык')
    product_code = models.CharField(max_length=255, verbose_name='Код товара')

    def __str__(self):
        return "{} : {}".format(self.category.name, self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')


class Order(models.Model):

    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обарботке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен')
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка'),
    )

    customer = models.ForeignKey(Customer, verbose_name='Покупатель', on_delete=models.CASCADE, related_name='related_orders')
    first_name = models.CharField(max_length=255, verbose_name='Имя')
    last_name = models.CharField(max_length=255, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    
    cart = models.ForeignKey(Cart, verbose_name='Корзина', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес', null=True, blank=True)
    status = models.CharField(
        max_length=100, 
        verbose_name='Статус заказа', 
        choices=STATUS_CHOICES, 
        default=STATUS_NEW
    )

    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )

    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')
    order_date = models.DateTimeField(verbose_name='Дата получения заказа', default=timezone.now)

    def __str__(self):
        return str(self.id)
