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
    import json
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings

    # 1. Handle Multipart/Form-Data vs JSON
    # If content-type is multipart/form-data, we expect 'data' (json) and files ('cover_image', 'epub_file')
    if request.content_type.startswith('multipart/form-data'):
        try:
            # Parse JSON data
            raw_data = request.data.get('data')
            if not raw_data:
                 return Response(
                    {"message": "JSON 데이터('data' 필드)가 누락되었습니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if isinstance(raw_data, str):
                data = json.loads(raw_data)
            else:
                data = raw_data # In case DRF parsed it already?

            # Handle File Uploads
            if 'cover_image' in request.FILES:
                cover_file = request.FILES['cover_image']
                # Save file
                path = default_storage.save(f"covers/{cover_file.name}", ContentFile(cover_file.read()))
                # Generate full URL
                data['cover_image'] = request.build_absolute_uri(settings.MEDIA_URL + path)
            
            if 'epub_file' in request.FILES:
                epub = request.FILES['epub_file']
                path = default_storage.save(f"epubs/{epub.name}", ContentFile(epub.read()))
                data['epub_file'] = request.build_absolute_uri(settings.MEDIA_URL + path)

        except json.JSONDecodeError:
             return Response(
                {"message": "JSON 형식이 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"message": f"파일 업로드 처리 중 오류 발생: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # Standard JSON request (backward compatibility or testing)
        data = request.data

    serializer = AdminBookCreateSerializer(data=data)
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


@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
@authentication_classes([JWTAuthentication])
def admin_author_list(request):
    """
    GET: 작가 목록 조회 (name 쿼리 파라미터로 검색)
    POST: 새 작가 생성 (이름만 입력 받아 생성)
    """
    if request.method == "GET":
        query = request.query_params.get("name", "").strip()
        if query:
            authors = Author.objects.filter(name__icontains=query)
        else:
            authors = Author.objects.all()[:50] # Limit default list

        from .admin_serializers import AdminAuthorListSerializer
        serializer = AdminAuthorListSerializer(authors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        name = request.data.get("name", "").strip()
        if not name:
             return Response({"message": "작가 이름을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)
        
        author, created = Author.objects.get_or_create(name=name, defaults={"bio": ""})
        
        from .admin_serializers import AdminAuthorListSerializer
        serializer = AdminAuthorListSerializer(author)
        
        return Response(
            {
                "message": "작가가 생성되었습니다." if created else "이미 존재하는 작가입니다.",
                "author": serializer.data
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )