import math
import datetime
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.core import files
from users.models import User

FIXED = 'fixed'
PERCENTUAL = 'percentual'
TAXRATE_AMOUNT_TYPES = ((FIXED, 'Fixed'), (PERCENTUAL, 'Percentual'),)
TAX_ROUNDING_STEP = 0.05
SETTING_TAX = 'tax'
SETTING_STOCK = 'stock'
SETTINGS_CATEGORIES = ((SETTING_TAX, 'Tax'), (SETTING_STOCK, 'Stock'),)
DEFAULT_BASE_PRICE_INCLUDES_TAX = False
DEFAULT_CURRENCY = 'USD'
TAX_CAXCULATION_MODE_SUM = 'sum'
TAX_CAXCULATION_MODE_CASCADE = 'cascade'
DEFAULT_TAX_RATES_CALCULATION_MODE = TAX_CAXCULATION_MODE_SUM #or cascade

class Exportable(object):
    """
    Simple interface to export classes as serializable dicts
    """
    EXPORT_FIELDS = []

    def export(self, fieldset=None):
        """
        """
        out = {}
        if fieldset is None:
            fieldset = self.EXPORT_FIELDS
        for fname, fsource in fieldset:
            val = getattr(self, fsource, None)
            if callable(val):
                val = val()
            elif isinstance(val, files.File):
                try:
                    val = val.url
                except ValueError:
                    val = None
            elif isinstance(val, (datetime.date, datetime.datetime)):
                val = val.isoformat()
            out[fname] = val
        return out

class GeneralSettings(models.Model):
    """
    General settings of the application
    E.g. for product prices, the the setting shall define whether the base_price includes taxes or not
    """
    setting_code = models.CharField(max_length=50)
    setting_value = models.CharField(max_length=50)
    category = models.CharField(max_length=50, choices=SETTINGS_CATEGORIES)

    @staticmethod
    def get_setting_value(setting_code):        
        resolved_value = None
        try:
            resolved_value = GeneralSettings.objects.get(setting_code=setting_code)
        except GeneralSettings.DoesNotExist:
            if setting_code == 'base_price_includes_taxes':
                resolved_value = DEFAULT_BASE_PRICE_INCLUDES_TAX
            elif setting_code == 'currency':
                resolved_value = DEFAULT_CURRENCY
            elif setting_code == 'tax_rates_calculation_mode':
                resolved_value = DEFAULT_TAX_RATES_CALCULATION_MODE
        return resolved_value

class TaxCalculator(object):
    """
    """   
    def round_up_nearest(self, number, step):
        """
        """
        return round(math.ceil(float(number) / step) * step, -int(math.floor(math.log10(step))))
    
    def get_tax_amount(self, price, tax_rate, quantity=1):
        """
        """
        if tax_rate.mode == PERCENTUAL:
            tax_amount = self.round_up_nearest(price * quantity * float(tax_rate.amount) / 100, TAX_ROUNDING_STEP)
        elif tax_rate.mode == FIXED:
            tax_amount = self.round_up_nearest(quantity * float(tax_rate.amount), TAX_ROUNDING_STEP)
        else:
            raise ValueError("Invalid Tax Rate mode")
        return tax_amount

    def get_tax_amount_from_price(self, price, tax_rate):
        """
        """
        if tax_rate.mode == PERCENTUAL:
            raw_tax_amount = price - (price / (1 + tax_rate.amount / 100))
            return self.round_up_nearest(raw_tax_amount, TAX_ROUNDING_STEP)
        elif tax_rate.mode == FIXED:
            return self.round_up_nearest(tax_rate.amount, TAX_ROUNDING_STEP)
        else:
            raise ValueError("Invalid Tax Rate mode")                        

class TaxRate(models.Model):
    """
    Tax rate for imported goods has to be applied after the basic sales tax
    Basic sales tax = 10%
    Additional tax for imported goods = 5%
    """
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=1, validators=[MinValueValidator(0.0)])
    mode = models.CharField(max_length=10, choices=TAXRATE_AMOUNT_TYPES)

    def __str__(self):
        return u'{}'.format(self.code)

class ProductCategory(models.Model):
    """
    Null Tax Rate is applicable to Books, Food and medical products
    """
    name = models.CharField(max_length=255)
    basic_tax_rate = models.ForeignKey(TaxRate, related_name='products', on_delete=models.CASCADE)
    additional_tax_rate = models.ForeignKey(TaxRate, related_name='products_imported', on_delete=models.CASCADE)

    def __str__(self):
        return u'{}'.format(self.name)

class Product(Exportable, TaxCalculator, models.Model):
    """
    As per default configuration, base_price does not include taxes and the display_price is
    the result of the application of taxes.
    is_imported field is included in Product class, as product is considered imported by
    the store before selling it.
    Additional custom duties related to international shippings are not a concern of this example
    and would hypotetically charged after sale.
    """
    EXPORT_FIELDS = (
        ('code', 'code'),
        ('name', 'name'),
        ('description', 'description'),
        ('base_price', 'base_price'),
        ('display_price', 'display_price'),
        ('currency', 'pcurrency'),
        ('category', 'pcategory'),
    )

    code = models.CharField(max_length=30)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    display_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_imported = models.BooleanField(default=False)
    category = models.ForeignKey(ProductCategory, related_name='products', on_delete=models.CASCADE)

    @property
    def pcurrency(self):
        return GeneralSettings.get_setting_value('currency')
    
    @property
    def pcategory(self):
        return self.category.name

    def __str__(self):
        return u'{} - {} - {}'.format(self.code, self.name, self.base_price)

    def get_applicable_taxes(self, quantity=1):
        """
        Return applicable taxes for a given product
        """        
        base_price_includes_taxes = GeneralSettings.get_setting_value('base_price_includes_taxes')
        if base_price_includes_taxes is False:
            product = self
            basic_tax_rate = product.category.basic_tax_rate
            base_tax_amount = self.get_tax_amount(float(product.base_price), basic_tax_rate, quantity)
            additional_tax_amount = 0
            if product.is_imported:
                additional_tax_rate = product.category.additional_tax_rate
                price_to_calculate = float(product.base_price)
                tax_rates_calculation_mode = GeneralSettings.get_setting_value('tax_rates_calculation_mode')
                if tax_rates_calculation_mode == TAX_CAXCULATION_MODE_CASCADE:
                    price_to_calculate = float(product.base_price) + base_tax_amount
                # else calculation mode is SUM
                additional_tax_amount = self.get_tax_amount(price_to_calculate, additional_tax_rate, quantity)
            return base_tax_amount, additional_tax_amount
        return 0, 0

class Cart(Exportable, TaxCalculator, models.Model):
    """
    """
    EXPORT_FIELDS = (
        ('customer', 'customer'),
        ('date', 'updated_at'),
        ('items', 'cart_items'),        
    )

    EXPORT_FIELDS_RECEIPT = (
        ('customer', 'customer'),
        ('date', 'updated_at'),
        ('data', 'receipt_data'),        
    )
    
    session_id = models.CharField(max_length=255)
    customer = models.ForeignKey(User, related_name='cart_association', null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def get_receipt(self):
        ritems = []
        total_price = 0
        total_tax_amount = 0
        for item in self.items.all():
            product = item.product
            receipt_item = product.export()
            base_tax_amount, additional_tax_amount = product.get_applicable_taxes(item.quantity)
            receipt_item['base_tax_amount'] = base_tax_amount
            receipt_item['additional_tax_amount'] = additional_tax_amount
            ritems.append(receipt_item)
            total_price += float(item.product.base_price) + base_tax_amount + additional_tax_amount
            total_tax_amount += base_tax_amount + additional_tax_amount
        return ritems, float('{0:.2f}'.format(total_price)), float('{0:.2f}'.format(total_tax_amount))
    
    @property
    def cart_items(self):
        return [item.product.export() for item in self.items.all()]

    @property
    def receipt_data(self):
        items, total_price, total_tax_amount = self.get_receipt()
        return {'total_price': total_price, 'total_tax_amount': total_tax_amount, 'items': items}

class CartItem(models.Model):
    """
    """
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_item_association', on_delete=models.CASCADE)
    quantity = models.IntegerField()
