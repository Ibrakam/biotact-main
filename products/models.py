from django.db import models
from django.utils import timezone


# Create your models here.
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('products', 'Продукт'),
        ('sets', 'Эксклюзивные сеты'),
        ('merch', 'Мерч'),
    ]
    product_name = models.CharField(max_length=50, blank=True)
    price = models.BigIntegerField(blank=True)
    description_ru = models.TextField(blank=True)
    description_uz = models.TextField(blank=True)
    product_image = models.FileField(upload_to="product_images")
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='products')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.product_name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'


class UserTG(models.Model):
    user_tg_id = models.BigIntegerField(blank=True, null=True)
    user_name = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    lang = models.CharField(default="ru", null=True, max_length=10)
    birthday = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_name

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class UsedPromocode(models.Model):
    user_id = models.BigIntegerField(blank=True, null=True)
    promocode = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.promocode

    class Meta:
        verbose_name = 'Использованный промокод'
        verbose_name_plural = 'Использованные промокоды'


class Promocode(models.Model):
    EXPIRATION_CHOICES = [
        ('time', 'По времени'),
        ('date', 'По дате'),
    ]

    promocode_code = models.CharField(max_length=50, blank=True, null=True)
    discount = models.BigIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expiration_type = models.CharField(max_length=4, choices=EXPIRATION_CHOICES, default='time')
    expiration_time = models.DurationField(null=True, blank=True, help_text="Продолжительность действия промокода (в днях)")
    expiration_date = models.DateTimeField(null=True, blank=True, help_text="Дата и время истечения промокода")

    def __str__(self):
        return self.promocode_code

    def is_expired(self):
        if self.expiration_type == 'time' and self.expiration_time:
            return timezone.now() > (self.created_at + self.expiration_time)
        elif self.expiration_type == 'date' and self.expiration_date:
            return timezone.now() > self.expiration_date
        return False

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'


class UserCart(models.Model):
    user_id = models.BigIntegerField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    promocode = models.CharField(max_length=50, blank=True, null=True)
    total_price = models.BigIntegerField(blank=True, null=True)
    products = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.products) if self.products else "No Product"

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class MyOrders(models.Model):
    user_id = models.BigIntegerField(blank=True, null=True)
    order_text = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return str(self.order_text) if self.order_text else "No Product"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class UserAddress(models.Model):
    user_id = models.BigIntegerField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)

    def __str__(self):
        return str(self.address) if self.address else "No Product"

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
