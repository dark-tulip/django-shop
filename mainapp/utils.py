from django.db import models


def recalc_cart(cart):
    # Все продукты в корзине - посчитать общую сумму
    cart_data = cart.products.aggregate(models.Sum('final_price'), models.Count('id'))
    print(cart_data)
    if cart_data['final_price__sum']:
        cart.final_price = cart_data['final_price__sum']
    else: 
        cart.final_price = 0

    cart.total_products = cart_data['id__count']   
    cart.save()    