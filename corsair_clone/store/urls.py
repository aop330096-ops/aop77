from django.urls import path

from . import views

app_name = "store"

urlpatterns = [
    path("", views.home, name="home"),
    path("products/", views.product_list, name="product_list"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("login/", views.login_choice, name="login_choice"),
    path("login/user/", views.user_login, name="user_login"),
    path("login/admin/", views.admin_login, name="admin_login"),
    path("signup/", views.signup, name="signup"),
    path("logout/", views.logout_view, name="logout"),
    path("cart/", views.cart_view, name="cart"),
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("remove-from-cart/<int:item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("update-cart/<int:item_id>/", views.update_cart_item, name="update_cart_item"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("place-order/", views.place_order, name="place_order"),
    path("order-success/<str:order_id>/", views.order_success, name="order_success"),
]
