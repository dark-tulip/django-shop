from django.db import transaction

from django.shortcuts import render
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from django.views.generic.detail import DetailView
from django.http import HttpResponseRedirect, request
from django.views.generic import View

from .models import Category, LatestProducts, Customer, Cart, Cartproduct, FictionBook, ScienceBook
from .mixins import CategoryDetailMixin, CartMixin
from .forms import OrderForm
from .utils import recalc_cart

# # Create your views here.

class BaseView(CartMixin, View):


    def get(self, request, *args, **kwargs):
        categories = Category.objects.get_categories_for_left_sidebar()
        products = LatestProducts.objects.get_products_for_main_page(
            'fictionbook', 'sciencebook', with_respect_to='smartphone'
        )

        context = {
            'categories': categories,
            'products': products,
            'cart': self.cart
        }
        return render(request, 'base.html', context)



class ProductDetailView(CartMixin, CategoryDetailMixin, DetailView):

    CT_MODEL_MODEL_CLASS = {
        'fictionbook': FictionBook,
        'sciencebook': ScienceBook
    }

    def dispatch(self, request, *args, **kwargs):
        self.model = self.CT_MODEL_MODEL_CLASS[kwargs['ct_model']]
        self.queryset = self.model._base_manager.all()
        return super().dispatch(request, *args, **kwargs)


    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'


    def get_context_data(self, **kwargs):
        # Инфа о конкретной модели
        context =  super().get_context_data(**kwargs)
        context['ct_model'] = self.model._meta.model_name
        context['cart'] = self.cart
        return context



class CategoryDetailView(CartMixin, CategoryDetailMixin, DetailView):

    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        # Инфа о конкретной модели
        context =  super().get_context_data(**kwargs)
        context['cart'] = self.cart
        return context


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug') # Название категории и модели товара
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)

        cart_product, created = Cartproduct.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )

        if created:
            self.cart.products.add(cart_product)            

        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно добавлен")
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug') # Название категории и модели товара
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)

        cart_product = Cartproduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )

        self.cart.products.remove(cart_product)
        cart_product.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно удален")


        return HttpResponseRedirect('/cart/')


class ChangeQTYView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug') # Название категории и модели товара
        content_type = ContentType.objects.get(model=ct_model)
        product = content_type.model_class().objects.get(slug=product_slug)

        cart_product = Cartproduct.objects.get(
            user=self.cart.owner, cart=self.cart, content_type=content_type, object_id=product.id
        )
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        # Обновить инфу в корзине после изменения количества cart-product
        cart_product.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Кол-во успешно изменено")

        
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):
    # Через юзера рендерим его корзину
    def get(self, request, *args, **kwargs):

        categories = Category.objects.get_categories_for_left_sidebar()
        context = {
            'cart': self.cart,
            'categories': categories
        }
        return render(request, 'cart.html', context)


class CheckoutView(CartMixin, View):
    # Через юзера рендерим его корзину
    def get(self, request, *args, **kwargs):

        categories = Category.objects.get_categories_for_left_sidebar()
        form = OrderForm(request.POST or None)
        context = {
            'cart': self.cart,
            'categories': categories,
            'form': form
        }
        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)

        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone = form.cleaned_data['phone']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.comment = form.cleaned_data['comment']
            
            new_order.save()
            self.cart.in_order = True
            self.cart.save()

            new_order.cart = self.cart
            new_order.save()

            customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Спасибо за заказ! С вами свяжется менеджер)')

            return HttpResponseRedirect('/')

        return HttpResponseRedirect('/checkout/')

