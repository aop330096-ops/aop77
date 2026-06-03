from .models import CartItem, Cart


def cart_count(request):
    count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).order_by("-created_at").first()
            if cart:
                count = sum(item.quantity for item in cart.items.all())
        else:
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.filter(session_key=session_key).order_by("-created_at").first()
                if cart:
                    count = sum(item.quantity for item in cart.items.all())
    except Exception:
        count = 0
    return {"cart_item_count": count}
