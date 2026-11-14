import time
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring

from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.utils.html import strip_tags
from django.views import View


FEED_FILE_NAME = 'merchant.xml'
FEED_MAX_AGE = 60 * 60


class FeedStrategy(View):
    """Google Merchant RSS feed.

    Subclass this view, set the feed title and description, and implement
    get_queryset plus the required product field methods. Override an
    optional field method when the project has that information. The shop
    domain is read from settings.DOMAIN.
    """

    title = ''
    description = ''
    file_name = FEED_FILE_NAME
    max_age = FEED_MAX_AGE
    product_fields = (
        'id',
        'title',
        'description',
        'link',
        'image_link',
        'availability',
        'price',
        'condition',
        'availability_date',
        'brand',
        'gtin',
        'mpn',
        'identifier_exists',
        'product_type',
        'google_product_category',
        'additional_image_link',
    )

    @property
    def host(self):
        return f'https://{settings.DOMAIN}'

    def get_queryset(self):
        raise NotImplementedError

    def get_id(self, product):
        raise NotImplementedError

    def get_title(self, product):
        raise NotImplementedError

    def get_description(self, product):
        raise NotImplementedError

    def get_link(self, product):
        raise NotImplementedError

    def get_image_link(self, product):
        raise NotImplementedError

    def get_availability(self, product):
        raise NotImplementedError

    def get_price(self, product):
        raise NotImplementedError

    def get_condition(self, product):
        return None

    def get_availability_date(self, product):
        return None

    def get_brand(self, product):
        return None

    def get_gtin(self, product):
        return None

    def get_mpn(self, product):
        return None

    def get_identifier_exists(self, product):
        return None

    def get_product_type(self, product):
        return None

    def get_google_product_category(self, product):
        return None

    def get_additional_image_link(self, product):
        return None

    def get_feed_path(self):
        return Path(settings.BASE_DIR) / 'tmp' / self.file_name

    def get(self, request, *args, **kwargs):
        path = self.get_feed_path()
        if self._is_stale(path):
            self.write_feed(path)

        try:
            data = path.read_bytes()
        except OSError:
            return HttpResponseNotFound()

        response = HttpResponse(data, content_type='application/xml')
        response['Content-Disposition'] = (
            f'attachment; filename="{self.file_name}"'
        )
        return response

    def _is_stale(self, path):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return True
        return time.time() - mtime > self.max_age

    def write_feed(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.render_feed())

    def render_feed(self):
        root = Element('rss', {
            'version': '2.0',
            'xmlns:g': 'http://base.google.com/ns/1.0',
        })
        channel = SubElement(root, 'channel')
        SubElement(channel, 'title').text = self.title
        SubElement(channel, 'link').text = self.host
        SubElement(channel, 'description').text = self.description

        for product in self.get_queryset():
            item = SubElement(channel, 'item')
            for name in self.product_fields:
                value = getattr(self, f'get_{name}')(product)
                self._append_field(item, name, value)

        return (
            b'<?xml version="1.0"?>\n'
            + tostring(root, encoding='utf-8', method='xml')
        )

    def _append_field(self, item, name, value):
        if isinstance(value, (list, tuple)):
            values = value
        else:
            values = [value]

        for entry in values:
            if isinstance(entry, str):
                entry = strip_tags(entry)
            if entry is None or entry == '':
                continue
            SubElement(item, f'g:{name}').text = str(entry)
