# Generated by Django 5.0.6 on 2024-07-18 13:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_alter_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(choices=[('products', 'Продукт'), ('sets', 'Эксклюзивные сеты'), ('merch', 'Мерч')], default='product', max_length=10),
        ),
    ]
