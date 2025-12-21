from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count

from api.models import Book, UserBookHistory


class Command(BaseCommand):
    help = "Update Book.readed_num_week (last 7 days)."

    def handle(self, *args, **options):
        now = timezone.now()
        start_dt = now - timedelta(days=7)

        # 1) 최근 7일에 읽은 기록을 book(=isbn) 기준으로 묶고 개수 세기
        rows = (
            UserBookHistory.objects
            .filter(last_read_at__gte=start_dt)
            .values("book")           
            .annotate(cnt=Count("id"))
        )

        # 2) 전체 책의 주간 수치를 0으로 초기화
        Book.objects.update(readed_num_week=0)

        # 3) 집계 결과가 있는 책만 업데이트
        for r in rows:
            isbn = r["book"]
            cnt = r["cnt"]
            Book.objects.filter(isbn=isbn).update(readed_num_week=cnt)

        self.stdout.write(self.style.SUCCESS("Weekly counts updated."))