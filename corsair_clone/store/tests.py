from django.test import TestCase
from django.urls import reverse
from store.models import Product, Cart, CartItem, Category

class StoreTests(TestCase):
    def test_home_view_renders_and_seeds(self):
        # Database should be seeded on home page request
        self.assertEqual(Product.objects.count(), 0)
        response = self.client.get(reverse("store:home"))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(Product.objects.count(), 0)
        
    def test_product_list_renders_and_seeds(self):
        # Database should be seeded on product list request
        self.assertEqual(Product.objects.count(), 0)
        response = self.client.get(reverse("store:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(Product.objects.count(), 0)
        
    def test_add_to_cart(self):
        # Seed DB first by hitting home page
        self.client.get(reverse("store:home"))
        product = Product.objects.first()
        self.assertIsNotNone(product)
        
        # Add to cart
        response = self.client.post(reverse("store:add_to_cart", args=[product.id]))
        self.assertRedirects(response, reverse("store:cart"))
        
        # Verify cart item exists
        cart = Cart.objects.first()
        self.assertIsNotNone(cart)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().product, product)
        self.assertEqual(cart.items.first().quantity, 1)

    def test_update_cart_item(self):
        self.client.get(reverse("store:home"))
        product = Product.objects.first()
        self.client.post(reverse("store:add_to_cart", args=[product.id]))
        cart_item = CartItem.objects.first()
        self.assertIsNotNone(cart_item)
        
        # Update quantity
        response = self.client.post(reverse("store:update_cart_item", args=[cart_item.id]), {"quantity": 3})
        self.assertRedirects(response, reverse("store:cart"))
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 3)

    def test_checkout_validation_error_preserves_context(self):
        # Set up a product and cart
        self.client.get(reverse("store:home"))
        product = Product.objects.first()
        self.client.post(reverse("store:add_to_cart", args=[product.id]))
        
        # Submit empty checkout form
        response = self.client.post(reverse("store:place_order"), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn("error", response.context)
        self.assertEqual(response.context["error"], "All fields are required.")
        # Ensure cart/pricing details are passed to avoid template errors
        self.assertIn("items", response.context)
        self.assertIn("subtotal", response.context)
        self.assertIn("grand_total", response.context)
