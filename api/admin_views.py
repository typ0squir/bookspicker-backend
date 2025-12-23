# api/admin_views.py
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.db import transaction

from .admin_serializers import AdminBookCreateSerializer
from .models import Book, GenreChild, Author, AuthorsBook


@api_view(["POST"])
@permission_classes([IsAdminUser])
@authentication_classes([JWTAuthentication])
def admin_book_create(request):
    serializer = AdminBookCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "message": "요청 값이 올바르지 않습니다.",
                "error": {"code": "INVALID_REQUEST", "details": serializer.errors},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    data = serializer.validated_data
    isbn = data["isbn"]

    if Book.objects.filter(isbn=isbn).exists():
        return Response(
            {
                "message": "이미 등록된 도서입니다.",
                "error": {"code": "BOOK_ALREADY_EXISTS"},
            },
            status=status.HTTP_409_CONFLICT,
        )

    try:
        genre_child = GenreChild.objects.get(id=data["genre_child_id"])
    except GenreChild.DoesNotExist:
        return Response(
            {
                "message": "갈래(genre)가 올바르지 않습니다.",
                "error": {"code": "INVALID_GENRE"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        # 1) Book 생성
        book = Book.objects.create(
            isbn=isbn,
            title=data["title"],
            subtitle=data.get("subtitle"),
            publisher=data["publisher"],

            toc=data["toc"],

            published_date=data["published_date"],
            page_count=data["page_count"],
            series_name=data.get("series_name"),
            lang=data["lang"],

            purchase_link=data.get("purchase_link"),
            genre=genre_child,

            cover_image=data["cover_image"],
            epub_file=data["epub_file"],

            abstract_descript=data.get("abstract_descript"),
            full_descript=data.get("full_descript"),
            top_tags=data.get("top_tags", []),
            recommendation_refer=data.get("recommendation_refer", []),
        )

        # 2) 작가 / 역할 / 대표작가
        for c in data["contributors"]:
            author, _ = Author.objects.get_or_create(
                name=c["name"].strip(),
                defaults={"bio": ""}  # bio 필수 필드 대응
            )

            AuthorsBook.objects.create(
                author=author,
                book=book,
                role=c["role"],
                is_primary=c["is_primary"],
            )

    return Response(
        {
            "message": "도서가 등록되었습니다.",
            "book": {
                "isbn": book.isbn,
                "title": book.title,
                "cover_image": book.cover_image,
                "epub_file": book.epub_file,
                "genre": str(book.genre),
                "toc_count": len(book.toc),
                "contributors_count": len(data["contributors"]),
            },
        },
        status=status.HTTP_201_CREATED,
    )