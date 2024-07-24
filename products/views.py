import json

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from products.bot.handlers.bot_commands import user_cart_from_tg
from .models import Product, UserCart

from rest_framework import generics
from .serializers import ProductSerializer


class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category', None)
        print(category)
        if category is not None:
            queryset = queryset.filter(category__iexact=category)
            print(queryset)
        return queryset


print(Product.objects.filter(category='products').all())


class ProductDetail(generics.RetrieveAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


def product_list(request):
    products = Product.objects.all()
    return render(request, 'all_products.html', {'products': products})


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_info.html', {'product': product})


def update_cart(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        action = request.POST.get('action')

        if product_id and action:
            product = get_object_or_404(Product, id=product_id)
            user_id = request.user.id  # Assuming user is authenticated

            cart_item, created = UserCart.objects.get_or_create(user_id=user_id, products=product)

            if action == 'add':
                cart_item.quantity = (cart_item.quantity or 0) + 1
            elif action == 'remove' and cart_item.quantity > 0:
                cart_item.quantity -= 1

            cart_item.total_price = cart_item.quantity * product.price
            cart_item.save()

            if cart_item.quantity == 0:
                cart_item.delete()

            return JsonResponse({
                'quantity': cart_item.quantity,
                'total_price': cart_item.total_price,
                'cart_total_items': UserCart.objects.filter(user_id=user_id).count()
            })

    return JsonResponse({'error': 'Invalid request'}, status=400)


import pandas as pd
from django.http import HttpResponse
from django.shortcuts import render
from products.models import UserTG  # Замените на ваши модели


def export_to_excel(request):
    # Получение данных из базы данных
    data = UserTG.objects.all().values()

    # Преобразование QuerySet в DataFrame
    df = pd.DataFrame(list(data))

    for column in df.select_dtypes(include=['datetimetz']).columns:
        df[column] = df[column].dt.tz_localize(None)

    # Создание HTTP-ответа с Excel файлом
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=my_data.xlsx'

    # Запись данных в Excel файл
    with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)

    return response


@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    data = json.loads(request.body)
    user_id = data['user_id']
    total_price = data['total_price']
    print(data['items'])

    for item in data['items']:
        product = Product.objects.get(id=item['id'])
        UserCart.objects.create(
            user_id=user_id,
            quantity=item['quantity'],
            total_price=item['price'] * item['quantity'],
            products=product
        )

    async_to_sync(user_cart_from_tg)(user_id=user_id)

    return JsonResponse({'status': 'success', 'message': 'Order created'})
