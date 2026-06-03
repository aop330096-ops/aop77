from django.conf import settings
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, get_user_model
from django.views.decorators.http import require_http_methods
from decimal import Decimal

from .models import Product, Cart, CartItem, Order, OrderItem

PRODUCTS = [
    {
        "name": "Phantom Gaming Keyboard",
        "slug": "phantom-gaming-keyboard",
        "description": "Mechanical tactile switches with intense neon cyan backlighting and premium aluminum-wrapped surfaces.",
        "price": "189.00",
        "image": "products/download.jpg",
        "highlights": [
            "Per-key dynamic lighting",
            "Dedicated macro controls",
            "Low-profile premium build"
        ],
    },
    {
        "name": "Titan X GPU Shroud",
        "slug": "titan-x-gpu-shroud",
        "description": "Extreme cooling performance with bold angular styling and a refined matte finish for serious gaming rigs.",
        "price": "429.00",
        "image": "products/download (1).jpg",
        "highlights": [
            "Advanced thermal channels",
            "RGB accent edge lighting",
            "Enhanced fan airflow"
        ],
    },
    {
        "name": "Vector Series NVMe SSD",
        "slug": "vector-series-nvme-ssd",
        "description": "High-bandwidth NVMe storage engineered for instant load times, rapid transfers, and sustained gaming throughput.",
        "price": "249.00",
        "image": "products/Gaming PC Essentials — High-Performance Desktops for Smooth Gameplay & Streaming.jpg",
        "highlights": [
            "3,500 MB/s read speed",
            "Shock-resistant durability",
            "Sleek low-profile heatsink"
        ],
    },
]


def _serialize_product(product):
    if isinstance(product, dict):
        return {
            "name": product["name"],
            "slug": product["slug"],
            "description": product["description"],
            "price": product["price"],
            "image": product["image"],
            "highlights": product.get("highlights", []),
        }

    return {
        "name": product.name,
        "slug": product.slug,
        "description": product.description,
        "price": str(product.price),
        "image": product.image.name if product.image else "",
        "id": product.id,
        "highlights": [],
    }


def _get_products():
    db_products = list(Product.objects.all())
    if not db_products:
        from .models import Category
        category, _ = Category.objects.get_or_create(name="Gaming Gear", slug="gaming-gear")
        for item in PRODUCTS:
            Product.objects.get_or_create(
                name=item["name"],
                slug=item["slug"],
                price=item["price"],
                description=item["description"],
                image=item["image"],
                category=category,
                stock_quantity=10,
            )
        db_products = list(Product.objects.all())
    return [_serialize_product(product) for product in db_products]


def home(request):
    """Landing page for the Corsair-inspired store."""
    products = _get_products()
    hero_product = products[0] if products else None
    trending_products = products
    desktop_highlights = products[:2]
    limited_deal = products[-1] if products else None
    return render(request, "store/home.html", {
        "hero_product": hero_product,
        "trending_products": trending_products,
        "desktop_highlights": desktop_highlights,
        "limited_deal": limited_deal,
        "products": products,
        "media_url": settings.MEDIA_URL,
    })


def product_list(request):
    """Product listing page placeholder."""
    return render(request, "store/products.html", {"products": _get_products(), "media_url": settings.MEDIA_URL})


def login_choice(request):
    """Allow users to choose between normal user auth and admin login."""
    return render(request, "store/login_choice.html")


@require_http_methods(["GET", "POST"])
def user_login(request):
    """Handle normal user login (GET shows form, POST attempts auth)."""
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        User = get_user_model()
        # Try authenticating using the provided value as username first
        user = authenticate(request, username=email, password=password)
        # If that fails, try to find a user with matching email and authenticate with their username
        if user is None:
            try:
                user_obj = User.objects.filter(email__iexact=email).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            except Exception:
                user = None
        if user is not None:
            auth_login(request, user)
            return redirect("store:home")
        error = "Invalid email or password"

    return render(request, "store/login_user.html", {"error": error})


@require_http_methods(["GET", "POST"])
def admin_login(request):
    """Handle admin login; only staff/superuser allowed."""
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, username=email, password=password)
        if user is None:
            try:
                User = get_user_model()
                user_obj = User.objects.filter(email__iexact=email).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
            except Exception:
                user = None
        if user is not None and (user.is_staff or user.is_superuser):
            auth_login(request, user)
            return redirect("store:home")
        error = "Invalid admin credentials"

    return render(request, "store/login_admin.html", {"error": error})


@require_http_methods(["GET", "POST"])
def signup(request):
    """Render signup page (GET) or create a new user and log them in (POST)."""
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        User = get_user_model()
        if not email or not password:
            error = "Email and password are required"
        elif User.objects.filter(username=email).exists():
            error = "A user with that email already exists"
        else:
            user = User.objects.create_user(username=email, email=email, password=password)
            auth_login(request, user)
            return redirect("store:home")

    return render(request, "store/signup.html", {"error": error})


def logout_view(request):
    """Log out current user and redirect to home."""
    auth_logout(request)
    return redirect("store:home")


def product_detail(request, slug):
    """Render product detail from database products or fallback static data."""
    product_obj = Product.objects.filter(slug=slug).first()
    if product_obj:
        product = _serialize_product(product_obj)
    else:
        product = next((item for item in PRODUCTS if item["slug"] == slug), None)
    if product is None:
        raise Http404("Product not found")
    return render(request, "store/product_detail.html", {"product": product, "media_url": settings.MEDIA_URL})


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    # ensure session exists
    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key
    cart, _ = Cart.objects.get_or_create(session_key=session_key)
    return cart


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = _get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect("store:cart")


def remove_from_cart(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    item.delete()
    return redirect("store:cart")


def update_cart_item(request, item_id):
    cart = _get_or_create_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)
    if request.method == "POST":
        try:
            qty = int(request.POST.get("quantity", item.quantity))
        except ValueError:
            qty = item.quantity
        if qty <= 0:
            item.delete()
        else:
            item.quantity = qty
            item.save()
    return redirect("store:cart")


def cart_view(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related("product").all()
    subtotal = sum(item.total_price() for item in items)
    tax = subtotal * Decimal("0.1")
    shipping = 0 if subtotal > 500 else 50
    grand_total = subtotal + tax + shipping
    return render(request, "store/cart.html", {
        "cart": cart,
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "grand_total": grand_total,
        "media_url": settings.MEDIA_URL,
    })


def checkout_view(request):
    cart = _get_or_create_cart(request)
    items = cart.items.select_related("product").all()
    if not items:
        return redirect("store:cart")
    subtotal = sum(item.total_price() for item in items)
    tax = subtotal * Decimal("0.1")
    shipping = 0 if subtotal > 500 else 50
    grand_total = subtotal + tax + shipping
    initial = {}
    if request.user.is_authenticated:
        user = request.user
        initial = {"full_name": user.get_full_name() or user.username, "email": user.email}
    return render(request, "store/checkout.html", {
        "items": items,
        "subtotal": subtotal,
        "tax": tax,
        "shipping": shipping,
        "grand_total": grand_total,
        "initial": initial,
    })


@require_http_methods(["POST"])
def place_order(request):
    # validate fields
    name = request.POST.get("full_name")
    email = request.POST.get("email")
    phone = request.POST.get("phone")
    address = request.POST.get("address")
    city = request.POST.get("city")
    state = request.POST.get("state")
    pincode = request.POST.get("pincode")
    payment_method = request.POST.get("payment_method")
    if not all([name, email, phone, address, city, state, pincode, payment_method]):
        cart = _get_or_create_cart(request)
        items = cart.items.select_related("product").all()
        subtotal = sum(item.total_price() for item in items)
        tax = subtotal * Decimal("0.1")
        shipping = 0 if subtotal > 500 else 50
        grand_total = subtotal + tax + shipping
        initial = {
            "full_name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "pincode": pincode,
            "payment_method": payment_method,
        }
        return render(request, "store/checkout.html", {
            "error": "All fields are required.",
            "items": items,
            "subtotal": subtotal,
            "tax": tax,
            "shipping": shipping,
            "grand_total": grand_total,
            "initial": initial,
        })

    cart = _get_or_create_cart(request)
    items = cart.items.select_related("product").all()
    if not items:
        return redirect("store:cart")

    subtotal = sum(item.total_price() for item in items)
    tax = subtotal * Decimal("0.1")
    shipping = 0 if subtotal > 500 else 50
    grand_total = subtotal + tax + shipping

    order = Order.objects.create(
        customer_name=name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        state=state,
        pincode=pincode,
        total_amount=grand_total,
        payment_method=payment_method,
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price,
        )

    # clear cart
    cart.items.all().delete()

    return redirect("store:order_success", order_id=order.order_id)


def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    return render(request, "store/order_success.html", {"order": order})
