from rest_framework import serializers

from .models import UserBookHistory


class CurrentReadingBookSerializer(serializers.ModelSerializer):
    isbn = serializers.CharField(source="book.isbn")
    title = serializers.CharField(source="book.title")
    publisher = serializers.CharField(source="book.publisher", allow_null=True)
    cover_image = serializers.URLField(source="book.cover_image", allow_null=True)

    # authors는 프로젝트에서 AuthorsBook 통해 가져올 가능성이 높아서,
    # 지금은 빈 리스트/확장 포인트로 둠
    authors = serializers.SerializerMethodField()

    resume_reading_url = serializers.SerializerMethodField()

    class Meta:
        model = UserBookHistory
        fields = [
            "isbn",
            "title",
            "authors",
            "publisher",
            "cover_image",
            "progress_percent",
            "resume_reading_url",
            "last_read_at",
        ]

    def get_authors(self, obj):
        # 추후 AuthorsBook 구조에 맞춰 구현:
        # 예: obj.book.authorsbook_set.filter(role="AUTHOR") ...
        return []

    def get_resume_reading_url(self, obj):
        isbn = obj.book.isbn
        loc = obj.current_location if obj.current_location is not None else 0
        # 프론트 라우팅 규칙에 맞게 수정
        return f"https://example.com/reader/{isbn}?loc={loc}"