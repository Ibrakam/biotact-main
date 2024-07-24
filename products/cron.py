from django.utils import timezone
from django.db.models import Q, F

from products.models import Promocode


def delete_expired_promocodes():
    expired_promocodes = Promocode.objects.filter(
        Q(expiration_type='time', created_at__lte=timezone.now() - F('expiration_time')) |
        Q(expiration_type='date', expiration_date__lte=timezone.now())
    )
    count = expired_promocodes.count()
    expired_promocodes.delete()
    print(f"Deleted {count} expired promocodes")
