from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .forms import RegisterForm, ProductForm
from .models import Product


def home(request):
    products = Product.objects.select_related('owner').prefetch_related('categories').all()
    return render(request, 'store/home.html', {'products': products})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})   # ← corregido


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('home')

    return render(request, 'store/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')


# =========================
# 🛒 Carrito
# =========================
def add_to_cart(request, product_id):          # ← NUEVA (la que faltaba)
    product = get_object_or_404(Product, pk=product_id)

    cart = request.session.get('cart', {})
    key = str(product.pk)
    cart[key] = cart.get(key, 0) + 1
    request.session['cart'] = cart

    return redirect('cart_detail')


def cart_detail(request):
    cart = request.session.get('cart', {})
    products = Product.objects.filter(pk__in=cart.keys())

    items = []
    total = 0
    for product in products:
        quantity = cart[str(product.pk)]
        subtotal = product.price * quantity    # cambia 'price' si tu campo se llama distinto
        total += subtotal
        items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})

    return render(request, 'store/cart_detail.html', {'items': items, 'total': total})


# =========================
# 📊 Dashboard
# =========================
@login_required
def dashboard(request):
    if not request.user.is_seller:
        return HttpResponseForbidden("No tienes permisos")

    products = Product.objects.filter(owner=request.user)
    return render(request, 'store/dashboard.html', {'products': products})


# =========================
# ➕ Crear producto
# =========================
@login_required
def product_create(request):
    if not request.user.is_seller:
        return HttpResponseForbidden("Solo vendedores")

    form = ProductForm(request.POST or None)

    if form.is_valid():
        product = form.save(commit=False)
        product.owner = request.user
        product.save()
        form.save_m2m()
        return redirect('dashboard')

    return render(request, 'store/product_form.html', {'form': form})


# =========================
# ✏️ Editar producto
# =========================
@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.owner != request.user:
        return HttpResponseForbidden("No puedes editar este producto")

    form = ProductForm(request.POST or None, instance=product)

    if form.is_valid():
        form.save()
        return redirect('dashboard')

    return render(request, 'store/product_form.html', {'form': form})


# =========================
# 🗑️ Eliminar producto
# =========================
@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if product.owner != request.user:
        return HttpResponseForbidden("No puedes eliminar este producto")

    if request.method == 'POST':
        product.delete()
        return redirect('dashboard')

    return render(request, 'store/product_confirm_delete.html', {'product': product})