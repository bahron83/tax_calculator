from django.views.decorators.cache import cache_page
from django.views.generic import View
from tax_calculator.utils import json_response
from tax_calculator.models import Cart


class ReceiptView(View):
    def get(self, request, *args, **kwargs):
        carts = Cart.objects.all()
        receipts = [cart.export(cart.EXPORT_FIELDS_RECEIPT) for cart in carts]
        out = {
            'receipts': receipts
        }
        return json_response(out)


CACHE_TTL = 120
receipt_view = cache_page(CACHE_TTL)(ReceiptView.as_view())
