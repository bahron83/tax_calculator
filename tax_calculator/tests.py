from django.test import TestCase
from tax_calculator.models import Cart, Product, TaxCalculator


class ProductTestCase(TestCase):
    fixtures = ['taxrate.json', 'product_category.json', 'product.json', 'cart.json', 'cart_item.json']
    
    def test_products_have_computable_taxes(self):        
        for product in Product.objects.all():
            base_tax_amount, additional_tax_amount = product.get_applicable_taxes()
            self.assertGreaterEqual(base_tax_amount, 0)
            self.assertGreaterEqual(additional_tax_amount, 0)
    
    def test_receipt_extraction(self):
        carts = Cart.objects.all()
        receipts = [cart.export(cart.EXPORT_FIELDS_RECEIPT) for cart in carts]
        self.assertEqual(len(receipts), 3)
        
        
