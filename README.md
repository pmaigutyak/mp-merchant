# MP-merchant

Django Google Merchant feed.

### Installation

Install with pip:

```
pip install django-mp-merchant
```

Add `merchant` to `INSTALLED_APPS`.

Set `DOMAIN` in settings. Product links are built as `https://<DOMAIN>`.

### Feed

Subclass `merchant.feed.FeedStrategy`. Set the feed title and description, implement `get_queryset`, and implement every required product field. Override an optional field when the shop has that information.

```python
from django.urls import path

from merchant.feed import FeedStrategy
from products.models import Product


class ProductFeed(FeedStrategy):

    title = 'Shop name'
    description = 'Shop description'

    def get_queryset(self):
        return Product.objects.filter(is_visible=True)

    def get_id(self, product):
        return product.pk

    def get_title(self, product):
        return product.name

    def get_description(self, product):
        return product.description

    def get_link(self, product):
        return f'{self.host}{product.get_absolute_url()}'

    def get_image_link(self, product):
        if not product.logo:
            return None
        return f'{self.host}{product.logo.url}'

    def get_availability(self, product):
        return 'in_stock' if product.is_available else 'out_of_stock'

    def get_price(self, product):
        return f'{product.price} UAH'

    def get_brand(self, product):
        if not product.manufacturer:
            return None
        return product.manufacturer.name


urlpatterns = [
    path('merchant.xml', ProductFeed.as_view(), name='feed'),
]
```

Required fields: `id`, `title`, `description`, `link`, `image_link`, `availability`, `price`.

Optional fields stay out of the file until overridden: `condition`, `availability_date`, `brand`, `gtin`, `mpn`, `identifier_exists`, `product_type`, `google_product_category`, `additional_image_link`.

Text is passed through `strip_tags`. A list is written as repeated elements. Empty values are skipped. The file is cached at `tmp/merchant.xml` for one hour.

Write `title` and `description` in the landing-page language. Attribute names and fixed values (`in_stock`, `new`, `UAH`) stay in English.

### Requirements

* Django
