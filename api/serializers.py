from rest_framework import serializers
from django.db.models import F
from .models import Book, Tag, BookTag, ReviewTag, Review

class BookTagInlineSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="tag.id")
    name = serializers.CharField(source="tag.name")
    tag_count = serializers.IntegerField()

    class Meta:
        model = BookTag
        fields = ["id", "name", "tag_count"]

class BookListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "subtitle",
            "series",
            "publisher",
            "genre",
            "cover_image",
            "page_count",
            "purchase_link",
            "published_date",
        ]

class BookDetailSerializer(serializers.ModelSerializer):
    tags = BookTagInlineSerializer(many=True, source="book_tags")

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "genre",
            "cover_image",
            "publisher",
            "published_date",
            "like_count",
            "full_descript",
            "tags",
        ]

class BookPopularSerializer(serializers.ModelSerializer):

    # TODO: 실제 Tag/BookTag 모델과 연결되면 여기서 Serializer로 교체
    tags = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    read_now_url = serializers.SerializerMethodField()
    wish_url = serializers.SerializerMethodField()
    purchase_url = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "cover_image",
            "tags",
            "two_line_descript",
            "like_count",
            "detail_url",
            "read_now_url",
            "wish_url",
            "purchase_url",
        ]

    # 실제 BookTag 목록 조회
    def get_tags(self, obj):
        book_tags = obj.book_tags.select_related("tag").all()
        return BookTagInlineSerializer(book_tags, many=True).data

    def get_detail_url(self, obj):
        # 프론트 도메인/라우팅 확정되면 그에 맞게 수정
        return f"https://example.com/books/{obj.isbn}"

    def get_read_now_url(self, obj):
        return f"https://example.com/reader/{obj.isbn}"

    def get_wish_url(self, obj):
        return f"https://example.com/users/wish/{obj.isbn}"

    def get_purchase_url(self, obj):
        # Book.purchase_link가 있으면 우선 사용
        if obj.purchase_link:
            return obj.purchase_link
        return f"https://example.com/store/{obj.isbn}"
    
class BookSearchSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    detail_url = serializers.SerializerMethodField()
    read_now_url = serializers.SerializerMethodField()
    wish_url = serializers.SerializerMethodField()
    purchase_url = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            "isbn",
            "title",
            "authors",
            "publisher",
            "cover_image",
            "detail_url",
            "read_now_url",
            "wish_url",
            "purchase_url",
        ]

    def get_authors(self, obj):
        # TODO: 실제 Author 테이블 연결되면 DB에서 불러오도록 변경
        # 현재는 더미 데이터 (책 한 권 = 작가 1명이라는 가정)
        return ["김영하"]

    def get_detail_url(self, obj):
        return f"https://example.com/books/{obj.isbn}"

    def get_read_now_url(self, obj):
        return f"https://example.com/reader/{obj.isbn}"

    def get_wish_url(self, obj):
        return f"https://example.com/users/wish/{obj.isbn}"

    def get_purchase_url(self, obj):
        return obj.purchase_link or f"https://example.com/store/{obj.isbn}"

class ReviewCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

class ReviewResponseSerializer(serializers.ModelSerializer):
    review_id = serializers.IntegerField(source="id")
    isbn = serializers.CharField(source="book.isbn")
    user = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "review_id",
            "isbn",
            "content",
            "created_at",
            "user",
            "tags",
            "is_owner",
        ]

    def get_user(self, obj):
        return {
            "nickname": obj.user.nickname,
            "profile_image": obj.user.profile_image if hasattr(obj.user, "profile_image") else None
        }

    def get_tags(self, obj):
        return [{"id": t.id, "name": t.name} for t in obj.tags.all()]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return request.user.is_authenticated and obj.user == request.user

class UserSummarySerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_pic = serializers.CharField

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name')

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    # 요청용: 태그 이름 리스트
    tags = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
    )

    # 응답용: 태그 상세 정보
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            'id',
            'content',
            'created_at',
            'updated_at',
            'user',
            'is_owner',
            'tags',   # write-only
            'tags_detail',      # read-only
        )

    def _sync_tags_and_booktags(self, review, tag_names, is_create=False):
        book = review.book

        # 새 태그 객체 불러오기/생성하기
        new_tags = []
        for name in tag_names:
            name = (name or "").strip()
            if not name:
                continue
            tag_obj, _ = Tag.objects.get_or_create(name=name)
            new_tags.append(tag_obj)

        new_set = set(new_tags)

        if is_create:
            # 리뷰 생성 시에는 모두 추가
            for tag in new_tags:
                ReviewTag.objects.get_or_create(review=review, tag=tag)
                book_tag, created = BookTag.objects.get_or_create(
                    book=book,
                    tag=tag,
                    defaults={"tag_count": 1},
                )
                if not created:
                    BookTag.objects.filter(pk=book_tag.pk).update(
                        tag_count=F("tag_count") + 1
                    )
        else:
            # 리뷰 수정 시에는 old/new 비교 필요
            old_tags = list(review.tags.all())
            old_set = set(old_tags)

            removed_tags = old_set - new_set
            added_tags = new_set - old_set

            # 제거된 태그 처리
            for tag in removed_tags:
                ReviewTag.objects.filter(review=review, tag=tag).delete()
                book_tag = BookTag.objects.filter(book=book, tag=tag).first()
                if book_tag:
                    BookTag.objects.filter(pk=book_tag.pk).update(
                        tag_count=F("tag_count") - 1
                    )

            # 추가된 태그 처리
            for tag in added_tags:
                ReviewTag.objects.get_or_create(review=review, tag=tag)
                book_tag, created = BookTag.objects.get_or_create(
                    book=book,
                    tag=tag,
                    defaults={"tag_count": 1},
                )
                if not created:
                    BookTag.objects.filter(pk=book_tag.pk).update(
                        tag_count=F("tag_count") + 1
                    )

        review.tags.set(new_tags)

    def get_is_owner(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.user == request.user)
    
    # tag관련 메서드
    def create(self, validated_data):
        # tag_ids 분리
        tag_names = validated_data.pop('tags', [])

        # 리뷰 생성
        review = Review.objects.create(**validated_data)

        self._sync_tags_and_booktags(review, tag_names, is_create=True)

        return review

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tags', None)

        # 다른 필드들 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 태그가 요청에 포함된 경우에만 태그 관계 갱신
        if tag_names is not None:
            self._sync_tags_and_booktags(instance, tag_names, is_create=False)

        return instance
