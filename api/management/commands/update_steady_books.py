from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count

from api.models import Book, UserBookHistory

STEADY_MIN_90D = 20  # 서비스 규모에 맞게 조절


class Command(BaseCommand):
    help = "Update Book.is_steady (based on last 90 days)."

    def handle(self, *args, **options):
        now = timezone.now()
        start_dt = now - timedelta(days=90)

        rows = (
            UserBookHistory.objects
            .filter(last_read_at__gte=start_dt)
            .values("book")
            .annotate(cnt=Count("id"))
        )

        Book.objects.update(is_steady=False)

        for r in rows:
            isbn = r["book"]
            cnt = r["cnt"]
            if cnt >= STEADY_MIN_90D:
                Book.objects.filter(isbn=isbn).update(is_steady=True)

        self.stdout.write(self.style.SUCCESS("Steady books updated."))