from decimal import Decimal

from django.db.models import Case, F
from django.db.models.expressions import When

from catalog.models import Product, get_price_sq


def get_products_annotated_prices(product_id_list):
    pr, ds, ds_type = get_price_sq('pk')
    return Product.objects.filter(id__in=product_id_list).annotate(pr=pr).annotate(
        annotate_price=Case(
            When(pr__isnull=False, then=pr),
            default=Decimal('0.00')
        )
    ).annotate(discount_value=ds, discount_type=ds_type).annotate(
        total_price=Case(
            When(pr__isnull=True, then=F('annotate_price')),
            When(discount_value=None, then=pr),
            When(discount_type=1, then=pr - pr * ds / 100),
            default=pr - ds
        )
    )