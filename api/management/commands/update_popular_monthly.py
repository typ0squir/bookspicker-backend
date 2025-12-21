from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count

from api.models import Book, UserBookHistory


class Command(BaseCommand):
    help = "Update Book.readed_num_month (last 30 days)."

    def handle(self, *args, **options):
        now = timezone.now()
        start_dt = now - timedelta(days=30)

        rows = (
            UserBookHistory.objects
            .filter(last_read_at__gte=start_dt)
            .values("book")
            .annotate(cnt=Count("id"))
        )

        Book.objects.update(readed_num_month=0)

        for r in rows:
            isbn = r["book"]
            cnt = r["cnt"]
            Book.objects.filter(isbn=isbn).update(readed_num_month=cnt)

        self.stdout.write(self.style.SUCCESS("Monthly counts updated."))