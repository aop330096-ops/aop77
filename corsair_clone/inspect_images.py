import os
import django

os.chdir(r'c:/Users/ADMIN/Desktop/op_pc/corsair_clone')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "corsair_clone.settings")
django.setup()

from store.views import _get_products
for product in _get_products():
    print(product['name'], product['image'])
