from django.conf import settings
import requests
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.utils import timezone
from django.contrib.auth import logout
from api.permissions import IsActiveUser

from .serializers import (
    ColdStartNicknameSerializer,
    ColdStartTagsSerializer,
    ColdStartBooksSerializer,
    ColdStartProfileInfoRequestSerializer,
    AccountCommentListItemSerializer,
    NicknameUpdateSerializer
)

User = get_user_model()

from .serializers import (
    ColdStartNicknameSerializer,
    ColdStartTagsSerializer,
    ColdStartBooksSerializer,
    ColdStartProfileInfoRequestSerializer,
    AccountCommentListItemSerializer,
    NicknameUpdateSerializer
)

from api.models import (
    Tag, Book, Highlight, UserBookHistory,
    Library, Wishlist, UserBookLike
)
from .models import Trait

def err(message, code, http_status):
    return Response(
        {"message": message},
        status=http_status
    )

# --------------------------
# ColdStart
# --------------------------
@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def coldstart_nickname(request):
    serializer = ColdStartNicknameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"message": "요청이 올바르지 않습니다.", "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    nickname = serializer.validated_data["nickname"]

    user = request.user
    user.nickname = nickname
    # 필요하면 "coldstart 완료" 같은 플래그도 여기서 함께 저장
    user.save(update_fields=["nickname"])

    return Response(
        {
            "message": "닉네임 설정 완료",
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
            },
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def coldstart_tags(request):
    serializer = ColdStartTagsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "message": "요청 형식이 올바르지 않습니다."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    trait, _ = Trait.objects.get_or_create(user=request.user)

    # 최초 1회 제한
    if trait.coldstart_done_at is not None or trait.coldstart_tags.exists():
        return Response(
            {
                "message": "선호 태그는 최초 1회만 설정할 수 있습니다."
            },
            status=status.HTTP_409_CONFLICT,
        )

    tag_ids = serializer.validated_data["tag_ids"]
    tags = list(Tag.objects.filter(id__in=tag_ids))

    if len(tags) != len(tag_ids):
        return Response(
            {
                "message": "존재하지 않는 태그가 포함되어 있습니다."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    trait.coldstart_tags.add(*tags)
    trait.coldstart_tags_done_at = timezone.now()
    trait.save(update_fields=["coldstart_tags_done_at"])

    return Response(
        {
            "message": "선호하는 태그가 성공적으로 설정되었습니다."
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def coldstart_books(request):
    serializer = ColdStartBooksSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"message": "요청 형식이 올바르지 않습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    trait, _ = Trait.objects.get_or_create(user=request.user)

    # 최초 1회 제한
    if getattr(trait, "coldstart_books_done_at", None) is not None or trait.coldstart_books.exists():
        return Response(
            {"message": "선호 책은 최초 1회만 설정할 수 있습니다."},
            status=status.HTTP_409_CONFLICT,
        )

    isbn_list = serializer.validated_data["isbn_list"]

    books = list(Book.objects.filter(isbn__in=isbn_list))
    found_isbns = {b.isbn for b in books}
    missing = [isbn for isbn in isbn_list if isbn not in found_isbns]
    if missing:
        return Response(
            {"message": "존재하지 않는 책이 포함되어 있습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 최초 입력: add()만 사용 (덮어쓰기 금지)
    trait.coldstart_books.add(*books)
    trait.coldstart_books_done_at = timezone.now()
    trait.save(update_fields=["coldstart_books_done_at"])

    return Response(
        {"message": "선호하는 책이 성공적으로 설정되었습니다."},
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def coldstart_profile_info(request):
    serializer = ColdStartProfileInfoRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {
                "message": "요청 값이 올바르지 않습니다.",
                "error": {"code": "INVALID_REQUEST", "details": serializer.errors},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    info = serializer.validated_data.get("profile_info", {})

    # 1) birth_year
    if "birth_year" in info:
        user.birth_year = str(info["birth_year"])

    # 2) sex
    if "sex" in info:
        user.sex = info["sex"]

    # 3) books_per_month
    if "books_per_month" in info:
        user.books_per_month = info["books_per_month"]

    user.save()


    return Response(
        {
            "message": "콜드스타트 추가 정보가 저장되었습니다.",
            "profile_info": {
                "birth_year": user.birth_year,
                "sex": user.sex,
                "books_per_month": user.books_per_month,
            },
        },
        status=status.HTTP_200_OK,
    )

# --------------------------
# Log
# --------------------------
@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def highlights_list(request):
    user = request.user

    # --- Query params (optional) ---
    try:
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        return Response(
            {
                "message": "요청 파라미터가 올바르지 않습니다.",
                "error": {"code": "INVALID_QUERY"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if limit < 1 or limit > 50:
        return Response(
            {
                "message": "limit은 1~50 사이여야 합니다.",
                "error": {"code": "INVALID_LIMIT"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if offset < 0:
        return Response(
            {
                "message": "offset은 0 이상이어야 합니다.",
                "error": {"code": "INVALID_OFFSET"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- Queryset ---
    qs = (
        Highlight.objects
        .select_related("book")
        .filter(user=user)
        .order_by("-created_at")
    )

    total_count = qs.count()
    items = qs[offset : offset + limit]

    highlights = []
    for h in items:
        highlights.append(
            {
                "highlight_id": h.id,

                # book 정보
                "isbn": getattr(h.book, "isbn", None),
                "book_title": getattr(h.book, "title", ""),
                "cover_image": getattr(h.book, "cover_image", None),

                # highlight 본문 + 좌표
                "content": h.content,
                "start_page": h.start_page,
                "end_page": h.end_page,
                "start_offset": h.start_offset,
                "end_offset": h.end_offset,

                "created_at": h.created_at,
            }
        )

    return Response(
        {
            "message": "내 하이라이트 목록 조회 성공",
            "meta": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
            },
            "highlights": highlights,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def comment_list(request):
    user = request.user

    # query params
    try:
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        return Response(
            {"message": "요청 파라미터가 올바르지 않습니다.", "error": {"code": "INVALID_QUERY"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if limit < 1 or limit > 50:
        return Response(
            {"message": "limit은 1~50 사이여야 합니다.", "error": {"code": "INVALID_LIMIT"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if offset < 0:
        return Response(
            {"message": "offset은 0 이상이어야 합니다.", "error": {"code": "INVALID_OFFSET"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # optional filters
    status_filter = request.GET.get("status")  # READING / FINISHED / STOPPED
    isbn_filter = request.GET.get("isbn")

    qs = (
        UserBookHistory.objects
        .select_related("book")
        .filter(user=user)
        .exclude(comment__isnull=True)
        .exclude(comment__exact="")
        .order_by("-updated_at")
    )

    if status_filter:
        qs = qs.filter(status=status_filter)

    if isbn_filter:
        qs = qs.filter(book__isbn=isbn_filter)

    total_count = qs.count()
    items = qs[offset: offset + limit]

    results = []
    for h in items:
        book = h.book
        results.append({
            "comment_id": h.id,
            "isbn": getattr(book, "isbn", ""),

            "content": h.comment,
            "created_at": h.created_at,
            "updated_at": h.updated_at,

            "status": h.status,
            "progress_percent": float(h.progress_percent),

            "book": {
                "isbn": getattr(book, "isbn", ""),
                "title": getattr(book, "title", ""),
                "cover_image": getattr(book, "cover_image", None),
                "publisher": getattr(book, "publisher", None),
            },
        })

    serializer = AccountCommentListItemSerializer(results, many=True)

    return Response(
        {
            "message": "내 코멘트 목록 조회 성공",
            "meta": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
            },
            "comments": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def booklist(request):
    """
    GET /accounts/booklist?filter=library|liked|wishlist|recent&limit=20&offset=0
    """
    user = request.user

    filter_type = request.GET.get("filter")
    allowed = ["library", "liked", "wishlist", "recent"]
    if filter_type not in allowed:
        return Response(
            {
                "message": "filter 값이 올바르지 않습니다.",
                "error": {"code": "INVALID_FILTER"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # pagination
    try:
        limit = int(request.GET.get("limit", 20))
        offset = int(request.GET.get("offset", 0))
    except ValueError:
        return Response(
            {"message": "요청 파라미터가 올바르지 않습니다.", "error": {"code": "INVALID_QUERY"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if limit < 1 or limit > 50:
        return Response(
            {"message": "limit은 1~50 사이여야 합니다.", "error": {"code": "INVALID_LIMIT"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if offset < 0:
        return Response(
            {"message": "offset은 0 이상이어야 합니다.", "error": {"code": "INVALID_OFFSET"}},
            status=status.HTTP_400_BAD_REQUEST,
        )


    # recent: UserBookHistory 기반
    if filter_type == "recent":
        qs = (
            UserBookHistory.objects
            .select_related("book")
            .filter(user=user)
            .exclude(last_read_at__isnull=True)
            .order_by("-last_read_at")
        )

        total_count = qs.count()
        items = qs[offset: offset + limit]

        books = []
        for h in items:
            b = h.book
            books.append({
                "isbn": getattr(b, "isbn", ""),
                "title": getattr(b, "title", ""),
                "cover_image": getattr(b, "cover_image", None),
                "publisher": getattr(b, "publisher", None),
                "last_read_at": h.last_read_at,
                "progress_percent": float(h.progress_percent),
            })

        return Response(
            {
                "message": "도서 목록 조회 성공",
                "filter": filter_type,
                "meta": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_next": (offset + limit) < total_count,
                },
                "books": books,
            },
            status=status.HTTP_200_OK,
        )


    # library / wishlist / liked: 연결 테이블 기반
    if filter_type == "library":
        link_qs = (
            Library.objects
            .select_related("book")
            .filter(user=user)
            .order_by("-added_at")
        )
        total_count = link_qs.count()
        items = link_qs[offset: offset + limit]

        books = []
        for link in items:
            b = link.book
            books.append({
                "isbn": getattr(b, "isbn", ""),
                "title": getattr(b, "title", ""),
                "cover_image": getattr(b, "cover_image", None),
                "publisher": getattr(b, "publisher", None),

                "added_at": link.added_at,
                "is_downloaded": bool(link.is_downloaded),
                "book_expiration_date": link.book_expiration_date,
            })

        return Response(
            {
                "message": "도서 목록 조회 성공",
                "filter": filter_type,
                "meta": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_next": (offset + limit) < total_count,
                },
                "books": books,
            },
            status=status.HTTP_200_OK,
        )

    if filter_type == "wishlist":
        link_qs = (
            Wishlist.objects
            .select_related("book")
            .filter(user=user)
            .order_by("-added_at")
        )
        total_count = link_qs.count()
        items = link_qs[offset: offset + limit]

        books = []
        for link in items:
            b = link.book
            books.append({
                "isbn": getattr(b, "isbn", ""),
                "title": getattr(b, "title", ""),
                "cover_image": getattr(b, "cover_image", None),
                "publisher": getattr(b, "publisher", None),

                "added_at": link.added_at,
            })

        return Response(
            {
                "message": "도서 목록 조회 성공",
                "filter": filter_type,
                "meta": {
                    "total_count": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_next": (offset + limit) < total_count,
                },
                "books": books,
            },
            status=status.HTTP_200_OK,
        )

    # filter_type == "liked"
    link_qs = (
        UserBookLike.objects
        .select_related("book")
        .filter(user=user)
        .order_by("-created_at")
    )
    total_count = link_qs.count()
    items = link_qs[offset: offset + limit]

    books = []
    for link in items:
        b = link.book
        books.append({
            "isbn": getattr(b, "isbn", ""),
            "title": getattr(b, "title", ""),
            "cover_image": getattr(b, "cover_image", None),
            "publisher": getattr(b, "publisher", None),

            "liked_at": link.created_at,
        })

    return Response(
        {
            "message": "도서 목록 조회 성공",
            "filter": filter_type,
            "meta": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_next": (offset + limit) < total_count,
            },
            "books": books,
        },
        status=status.HTTP_200_OK,
    )

# --------------------------
# Personal Info
# --------------------------
@api_view(["PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def nickname_update(request):
    serializer = NicknameUpdateSerializer(data=request.data, context={"request": request})
    if not serializer.is_valid():
        return Response(
            {
                "message": "요청 값이 올바르지 않습니다.",
                "error": {"code": "INVALID_REQUEST", "details": serializer.errors},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = request.user
    user.nickname = serializer.validated_data["nickname"]
    user.save(update_fields=["nickname"])

    return Response(
        {
            "message": "닉네임이 변경되었습니다.",
            "user": {
                "id": user.id,
                "nickname": user.nickname,
            },
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def resign(request):
    """
    요청 바디
    {
        "confirm": true,
        "refresh": "<refresh_token>"
    }
    """
    user = request.user

    # 1) 탈퇴 확인
    if request.data.get("confirm") is not True:
        return Response(
            {"message": "탈퇴 확인이 필요합니다.", "error": {"code": "CONFIRM_REQUIRED"}},
            status=400,
        )

    # 2) refresh 블랙리스트
    refresh_str = request.data.get("refresh")
    if refresh_str:
        try:
            RefreshToken(refresh_str).blacklist()
        except TokenError:
            # 이미 만료 / 잘못된 토큰이어도 탈퇴는 진행
            pass

    # 3) 사용자 탈퇴 처리
    user.is_active = False
    user.resigned_at = timezone.now()
    user.save(update_fields=["is_active", "resigned_at"])

    # 4) 세션 로그아웃 (마지막)
    logout(request)

    return Response(
        {"message": "회원 탈퇴가 완료되었습니다."},
        status=200,
    )


# --------------------------
# Social Login
# --------------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def social_login(request):
    """
    POST /accounts/social-login/
    Body: { "code": "..." }
    """
    code = request.data.get("code")
    if not code:
        return Response({"message": "code is required"}, status=400)

    # 1. Exchange code for access token
    token_req_url = "https://oauth2.googleapis.com/token"
    token_req_data = {
        "code": code,
        "client_id": getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", ""),
        "client_secret": getattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", ""),
        "redirect_uri": getattr(settings, "GOOGLE_OAUTH_REDIRECT_URI", ""),
        "grant_type": "authorization_code",
    }
    
    token_resp = requests.post(token_req_url, data=token_req_data)
    if not token_resp.ok:
        return Response(
            {"message": "Failed to get token from Google", "details": token_resp.json()},
            status=400
        )
    
    token_json = token_resp.json()
    google_access_token = token_json.get("access_token")

    # 2. Get User Info
    user_info_req_url = "https://www.googleapis.com/userinfo/v2/me"
    user_info_resp = requests.get(
        user_info_req_url, 
        params={"access_token": google_access_token}
    )
    if not user_info_resp.ok:
        return Response(
            {"message": "Failed to get user info from Google", "details": user_info_resp.json()},
            status=400
        )
    
    user_info = user_info_resp.json()
    email = user_info.get("email")
    name = user_info.get("name", "")

    if not email:
        return Response({"message": "Email not provided by Google"}, status=400)

    # 3. Find or Create User
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=email,
            email=email,
            password=None, 
        )
        if hasattr(user, 'first_name'):
             user.first_name = name 
        user.save()

    # 4. Generate JWT
    refresh = RefreshToken.for_user(user)

    return Response({
        "message": "Login Success",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        "token": {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
    })






