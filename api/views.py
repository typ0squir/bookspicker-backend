import os
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from datetime import timedelta

from ebooklib import epub
from bs4 import BeautifulSoup

from .models import (
    Book, AuthorsBook, BookTag, Tag,
    UserBookHistory, UserBookLike, Wishlist,
    Library, UserBookHistory, UserBookTag
)
from .permissions import IsActiveUser
from .constants import MAIN_BANNERS
from .serializers import (
    CurrentReadingBookSerializer,
    BookCommentDetailSerializer,
    PopularBookSerializer,
    BookSearchSerializer,
)

MAX_COMMENT_LENGTH = 280
LIST_LIMIT = 30 # 인기 목록을 최대 30권까지만
TOP_TAGS_LIMIT = 3

# 검색 결과 갯수 제한
DEFAULT_LIMIT = 20
MAX_LIMIT = 50

BANNER_LIMIT = 4

def error_response(message, code, status_code):
    return Response(
        {
            "message": message,
            "error": {"code": code},
        },
        status=status_code,
    )

# --------------------------
# Books
# --------------------------
@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([])
def book_detail(request, isbn):

    # Book 조회
    try:
        book = Book.objects.select_related("genre__parent").get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {"message": "도서를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 장르 경로
    genre_path = None
    if book.genre and book.genre.parent:
        genre_path = f"{book.genre.parent.name} > {book.genre.name}"

    # 작가 목록
    authors_qs = (
        AuthorsBook.objects
        .select_related("author")
        .filter(book=book)
    )

    authors = []
    for ab in authors_qs:
        authors.append({
            "author_id": ab.author.id,
            "name": ab.author.name,
            "role": ab.role,
            "bio": ab.author.bio,
            "detail_url": f"https://example.com/books/author/{ab.author.id}",
        })

    # 태그 목록
    book_tags_qs = (
        BookTag.objects
        .select_related("tag")
        .filter(
            book=book,
            tag__status="ACTIVE",
        )
        .order_by("-tag_count")[:15]
    )

    book_tags = []
    for bt in book_tags_qs:
        book_tags.append({
            "id": bt.tag.id,
            "name": bt.tag.name,
            "tag_count": bt.tag_count,
        })

    # 좋아요 여부
    is_liked = False
    if request.user.is_authenticated:
        is_liked = UserBookLike.objects.filter(
            user=request.user,
            book=book
        ).exists()

    # 댓글 (UserBookHistory.comment 기반)
    comments_qs = (
        UserBookHistory.objects
        .select_related("user")
        .filter(
            book=book,
            comment__isnull=False,
        )
        .exclude(comment__exact="")
        .order_by("-last_read_at", "-id")
    )

    comments = []
    for h in comments_qs:
        comments.append({
            "comment_id": h.id,  # UserBookHistory.id
            "user": {
                "id": h.user.id,
                "nickname": h.user.nickname,
                "profile_image": h.user.profile_image,
            },
            "created_at": h.last_read_at,
            "content": h.comment,
            "is_owner": (
                request.user.is_authenticated
                and request.user.id == h.user.id
            ),
        })

    is_wished = False
    if request.user.is_authenticated:
        is_wished = Wishlist.objects.filter(user=request.user, book=book).exists()

    # 응답
    response = {
        "message": "도서 상세 정보 조회 성공",
        "book": {
            "isbn": book.isbn,
            "title": book.title,
            "genre_path": genre_path,
            "cover_image": book.cover_image,

            "authors": authors,

            "publisher": book.publisher,
            "published_date": book.published_date,

            "like_count": book.like_count,
            "is_liked": is_liked,
            "is_wished": is_wished,

            "action_urls": {
                "read_now_url": f"https://example.com/reader/{book.isbn}",
                "wish_url": f"https://example.com/users/wish/{book.isbn}",
                "purchase_url": book.purchase_link,
            },

            # 임시 더미 (추후 추천/AI 로직으로 대체)
            "why_picked": {
                "body": (
                    "최근 닉네임님이 고른 책들을 보면, "
                    "사람 사이의 따뜻함과 조용한 연민이 스며든 "
                    "이야기들을 자주 선택하시는 느낌이었어요. "
                    "이 책은 그런 취향과 잘 맞는 작품이에요."
                )
            },

            "book_tags": book_tags,

            "description": book.full_descript,

            "comments": comments,
            "comment_count": len(comments),
        }
    }

    return Response(response, status=status.HTTP_200_OK)

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_like_toggle(request, isbn):
    # 1. 책 조회
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {"message": "도서를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    with transaction.atomic():
        like_qs = UserBookLike.objects.select_for_update().filter(
            user=request.user,
            book=book
        )

        # 2. 이미 좋아요 상태 → 취소
        if like_qs.exists():
            like_qs.delete()
            Book.objects.filter(
                isbn=book.isbn,
                like_count__gt=0
            ).update(like_count=F("like_count") - 1)

            book.refresh_from_db(fields=["like_count"])
            return Response(
                {
                    "message": "좋아요 상태가 변경되었습니다.",
                    "like_count": book.like_count,
                    "is_liked": False,
                },
                status=status.HTTP_200_OK,
            )

        # 3. 좋아요 안 한 상태 → 생성
        UserBookLike.objects.create(user=request.user, book=book)
        Book.objects.filter(isbn=book.isbn).update(
            like_count=F("like_count") + 1
        )

    book.refresh_from_db(fields=["like_count"])
    return Response(
        {
            "message": "좋아요 상태가 변경되었습니다.",
            "like_count": book.like_count,
            "is_liked": True,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_wishlist_toggle(request, isbn):
    # 1) 책 존재 확인
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {"message": "도서를 찾을 수 없습니다."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2) 토글
    with transaction.atomic():
        qs = Wishlist.objects.select_for_update().filter(
            user=request.user,
            book=book
        )

        # 이미 찜 상태 -> 삭제
        if qs.exists():
            qs.delete()
            return Response(
                {
                    "message": "찜 상태가 변경되었습니다.",
                    "is_wished": False,
                },
                status=status.HTTP_200_OK,
            )

        # 찜 안 한 상태 -> 추가
        Wishlist.objects.create(user=request.user, book=book)
        return Response(
            {
                "message": "찜 상태가 변경되었습니다.",
                "is_wished": True,
            },
            status=status.HTTP_200_OK,
        )

def normalize_tag_name(name: str) -> str:
    # 최소 정규화(추후 확장 가능)
    return name.strip().lower().replace(" ", "")

def resolve_canonical_tag(tag: Tag) -> Tag | None:
    """
    - BLOCKED: 사용 불가(None 반환)
    - MERGED: canonical로 치환
    - ACTIVE: 그대로 사용
    """
    if getattr(tag, "status", "ACTIVE") == "BLOCKED":
        return None
    if getattr(tag, "status", "ACTIVE") == "MERGED" and getattr(tag, "canonical", None):
        return tag.canonical
    return tag

def resolve_tags_from_payload(tags_payload) -> list[Tag]:
    """
    request.data["tags"]에서 existing_tag_ids / new_tag_names를 받아
    최종(Tag, canonical 반영) 리스트를 만든다.
    """
    if not isinstance(tags_payload, dict):
        tags_payload = {}

    existing_tag_ids = tags_payload.get("existing_tag_ids") or []
    new_tag_names = tags_payload.get("new_tag_names") or []

    resolved = []

    # 1) 기존 태그 ID
    if isinstance(existing_tag_ids, list):
        for tid in existing_tag_ids:
            tag_obj = Tag.objects.filter(id=tid).first()
            if not tag_obj:
                continue
            canonical = resolve_canonical_tag(tag_obj)
            if canonical:
                resolved.append(canonical)

    # 2) 신규 태그 이름
    if isinstance(new_tag_names, list):
        for raw_name in new_tag_names:
            name = (raw_name or "").strip()
            if not name:
                continue

            norm = normalize_tag_name(name)
            tag_obj = Tag.objects.filter(normalized=norm).first()

            if tag_obj is None:
                tag_obj = Tag.objects.create(
                    name=name,
                    normalized=norm,
                    status="ACTIVE",
                    global_count=0,
                )

            canonical = resolve_canonical_tag(tag_obj)
            if canonical:
                resolved.append(canonical)

    # canonical 중복 제거 (id 기준)
    resolved = list({t.id: t for t in resolved}.values())
    return resolved

def sync_user_book_tags(*, user, book, new_tags: list[Tag]):
    """
    정합성의 핵심.
    - old: UserBookTag에 저장된 (user, book)의 태그들
    - new: 이번 요청에서 확정된 최종 태그들
    diff만큼만 BookTag.user_count / tag_count를 증감한다.
    user-book 기준으로 태그를 최종 상태(new_tags)로 동기화
    """
    old_tag_ids = set(
        UserBookTag.objects
        .filter(user=user, book=book)
        .values_list("tag_id", flat=True)
    )

    new_tag_ids = set(tag.id for tag in new_tags)

    to_add = new_tag_ids - old_tag_ids
    to_remove = old_tag_ids - new_tag_ids

    # 추가
    for tag_id in to_add:
        UserBookTag.objects.create(user=user, book=book, tag_id=tag_id)

        bt, _ = BookTag.objects.get_or_create(book=book, tag_id=tag_id)
        BookTag.objects.filter(id=bt.id).update(
            user_count=F("user_count") + 1,
            tag_count=F("base_count") + (F("user_count") + 1),
        )
        Tag.objects.filter(id=tag_id).update(
            global_count=F("global_count") + 1
        )

    # 제거
    for tag_id in to_remove:
        UserBookTag.objects.filter(
            user=user, book=book, tag_id=tag_id
        ).delete()

        bt = BookTag.objects.filter(book=book, tag_id=tag_id).first()
        if bt:
            if bt.user_count > 0:
                BookTag.objects.filter(id=bt.id).update(
                    user_count=F("user_count") - 1,
                    tag_count=F("base_count") + (F("user_count") - 1),
                )
            else:
                BookTag.objects.filter(id=bt.id).update(
                    user_count=0,
                    tag_count=F("base_count"),
                )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_comment_create(request, isbn):
    # 1) 도서 조회
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response({"message": "도서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 2) content 검증
    content = (request.data.get("content") or "").strip()
    if not content:
        return Response({"message": "코멘트 내용은 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)
    if len(content) > MAX_COMMENT_LENGTH:
        return Response(
            {"message": f"코멘트는 최대 {MAX_COMMENT_LENGTH}자까지 작성할 수 있습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3) 유저당 1개 코멘트 제한
    already = (
        UserBookHistory.objects
        .filter(user=request.user, book=book)
        .exclude(comment__isnull=True)
        .exclude(comment__exact="")
        .exists()
    )
    if already:
        return Response({"message": "이미 이 도서에 코멘트를 작성하셨습니다."}, status=status.HTTP_409_CONFLICT)

    tags_payload = request.data.get("tags") or {}
    resolved_tags = resolve_tags_from_payload(tags_payload)

    now = timezone.now()

    with transaction.atomic():
        # 4) history 생성/갱신
        history, _ = UserBookHistory.objects.get_or_create(
            user=request.user,
            book=book,
            defaults={"started_at": now, "progress_percent": 0.0},
        )
        history.comment = content
        history.last_read_at = now
        history.save(update_fields=["comment", "last_read_at", "updated_at"])

        # 5) 태그 최종 상태 반영 (생성: old=없음 -> new=입력)
        sync_user_book_tags(user=request.user, book=book, new_tags=resolved_tags)

    return Response(
        {
            "message": "도서 코멘트가 등록되었습니다.",
            "comment_id": history.id,
        },
        status=status.HTTP_201_CREATED,
    )

@api_view(["PUT", "PATCH"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_comment_edit(request, isbn, comment_id):
    # 1) 도서 조회
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response({"message": "도서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 2) 본인 코멘트(history)인지 확인 (comment_id = UserBookHistory.id)
    history = UserBookHistory.objects.filter(id=comment_id, user=request.user, book=book).first()
    if not history:
        return Response({"message": "코멘트를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 3) content 검증
    content = (request.data.get("content") or "").strip()
    if not content:
        return Response({"message": "코멘트 내용은 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)
    if len(content) > MAX_COMMENT_LENGTH:
        return Response(
            {"message": f"코멘트는 최대 {MAX_COMMENT_LENGTH}자까지 작성할 수 있습니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    tags_payload = request.data.get("tags") or {}
    resolved_tags = resolve_tags_from_payload(tags_payload)

    with transaction.atomic():
        # 4) 코멘트 수정
        history.comment = content
        history.save(update_fields=["comment", "updated_at"])

        # 5) 태그 최종 상태로 동기화 (수정: old<->new diff만 반영)
        sync_user_book_tags(user=request.user, book=book, new_tags=resolved_tags)

    return Response({"message": "도서 코멘트가 수정되었습니다."}, status=status.HTTP_200_OK)

@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_comment_delete(request, isbn, comment_id):
    # 1) 도서 조회
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response({"message": "도서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    # 2) 본인 코멘트(history)인지 확인
    history = UserBookHistory.objects.filter(id=comment_id, user=request.user, book=book).first()
    if not history:
        return Response({"message": "코멘트를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        # 3) 코멘트 내용만 삭제 (히스토리는 유지)
        history.comment = None  # 또는 ""로 통일해도 됨. 생성의 already 체크와 맞추는 게 중요
        history.save(update_fields=["comment", "updated_at"])

        # 4) 태그 전부 제거 (old -> empty)
        sync_user_book_tags(user=request.user, book=book, new_tags=[])

    return Response({"message": "도서 코멘트가 삭제되었습니다."}, status=status.HTTP_200_OK)

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def book_comment_detail(request, isbn, comment_id):
    # 1) book 확인
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {
                "message": "도서를 찾을 수 없습니다.",
                "error": {"code": "BOOK_NOT_FOUND"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2) UserBookHistory에서 comment_id(pk)로 찾되 book 일치까지 강제
    try:
        history = (
            UserBookHistory.objects
            .select_related("user", "book")
            .get(id=comment_id, book=book)
        )
    except UserBookHistory.DoesNotExist:
        return Response(
            {
                "message": "코멘트를 찾을 수 없습니다.",
                "error": {"code": "COMMENT_NOT_FOUND"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # 3) comment가 비어있는 레코드는 '코멘트'로 취급하지 않음
    if history.comment is None or str(history.comment).strip() == "":
        return Response(
            {
                "message": "코멘트를 찾을 수 없습니다.",
                "error": {"code": "COMMENT_NOT_FOUND"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # 4) is_owner
    is_owner = bool(
        request.user.is_authenticated and history.user_id == request.user.id
    )

    payload = {
        "comment_id": history.id,
        "isbn": book.isbn,

        "content": history.comment,
        "created_at": history.created_at,
        "updated_at": history.updated_at,

        "is_owner": is_owner,

        "user": {
            "id": history.user.id,
            "nickname": getattr(history.user, "nickname", None) or getattr(history.user, "username", ""),
            "profile_image": getattr(history.user, "profile_image", None),
        },
        "book": {
            "isbn": book.isbn,
            "title": getattr(book, "title", ""),
            "cover_image": getattr(book, "cover_image", None),
        },
    }

    serializer = BookCommentDetailSerializer(payload)
    return Response(
        {
            "message": "도서 코멘트 조회 성공",
            "comment": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_comment_delete(request, isbn, comment_id):
    # 1) 책 존재 확인
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {"message": "도서를 찾을 수 없습니다.", "error": {"code": "BOOK_NOT_FOUND"}},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2) 해당 책의 해당 comment_id(UserBookHistory) 찾기
    try:
        history = UserBookHistory.objects.get(id=comment_id, book=book)
    except UserBookHistory.DoesNotExist:
        return Response(
            {"message": "코멘트를 찾을 수 없습니다.", "error": {"code": "COMMENT_NOT_FOUND"}},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 3) 본인 기록인지 확인
    if history.user_id != request.user.id:
        return Response(
            {"message": "삭제 권한이 없습니다.", "error": {"code": "FORBIDDEN"}},
            status=status.HTTP_403_FORBIDDEN,
        )

    # 4) 코멘트가 이미 없으면 삭제할 게 없음
    if not history.comment:
        return Response(
            {"message": "이미 삭제되었거나 코멘트가 없습니다.", "error": {"code": "COMMENT_NOT_FOUND"}},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 5) 코멘트만 삭제 (레코드는 유지)
    history.comment = None
    history.save(update_fields=["comment", "updated_at"])

    return Response(
        {
            "message": "도서 코멘트가 삭제되었습니다.",
            "isbn": book.isbn,
            "comment_id": history.id,
        },
        status=status.HTTP_200_OK,
    )

# tag 뱃지 color picker
def _pick_color(slug: str) -> str:
    """
    slug(normalized) 기반으로 항상 같은 색을 반환.
    DB에 color 필드 추가 전까지 사용하는 정책.
    """
    palette = [
        "#E57373", "#F06292", "#BA68C8", "#9575CD",
        "#7986CB", "#64B5F6", "#4FC3F7", "#4DD0E1",
        "#4DB6AC", "#81C784", "#AED581", "#DCE775",
        "#FFF176", "#FFD54F", "#FFB74D", "#A1887F",
    ]
    acc = 0
    for ch in slug:
        acc = (acc * 31 + ord(ch)) % 10_000_000
    return palette[acc % len(palette)]

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def books_popular(request):
    q = request.GET.get("q", "weekly")

    if q not in ["weekly", "monthly", "steady"]:
        return Response(
            {
                "message": "잘못된 요청입니다.",
                "error": {"code": "INVALID_QUERY_PARAM", "field": "q"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 1) q에 따라 Book queryset 결정
    if q == "weekly":
        books_qs = (
            Book.objects
            .filter(readed_num_week__gt=0)
            .order_by("-readed_num_week", "-like_count")
        )
    elif q == "monthly":
        books_qs = (
            Book.objects
            .filter(readed_num_month__gt=0)
            .order_by("-readed_num_month", "-like_count")
        )
    else:  # steady
        books_qs = (
            Book.objects
            .filter(is_steady=True)
            .order_by("-readed_num_month", "-like_count")
        )

    books = list(books_qs[:LIST_LIMIT])
    book_isbns = [b.isbn for b in books]

    if not books:
        return Response(
            {"message": "많이 읽힌 도서 목록 조회 성공", "query": q, "items": []},
            status=status.HTTP_200_OK,
        )

    # 2) top_tags 구성 (기존 정책 유지)
    booktags = (
        BookTag.objects
        .select_related("tag", "tag__canonical")
        .filter(book__isbn__in=book_isbns)
        .order_by("-tag_count", "tag__name")
    )

    top_tags_map = {}
    seen_canonical_map = {}

    for bt in booktags:
        isbn = bt.book_id
        tag = bt.tag

        if tag.status == "BLOCKED":
            continue

        canonical = (
            tag.canonical
            if tag.status == "MERGED" and tag.canonical_id
            else tag
        )

        if canonical.status == "BLOCKED":
            continue

        if isbn not in top_tags_map:
            top_tags_map[isbn] = []
            seen_canonical_map[isbn] = set()

        if canonical.id in seen_canonical_map[isbn]:
            continue

        slug = canonical.normalized
        top_tags_map[isbn].append({
            "id": canonical.id,
            "name": canonical.name,
            "slug": slug,
            "color": _pick_color(slug),
        })
        seen_canonical_map[isbn].add(canonical.id)

        if len(top_tags_map[isbn]) >= TOP_TAGS_LIMIT:
            continue

    # 3) is_liked 계산
    liked_isbn_set = set()
    if request.user.is_authenticated:
        liked_isbn_set = set(
            UserBookLike.objects
            .filter(user=request.user, book__isbn__in=book_isbns)
            .values_list("book__isbn", flat=True)
        )

    # 4) 응답 조립
    results = []
    for book in books:
        isbn = book.isbn
        results.append({
            "isbn": isbn,
            "title": book.title,
            "cover_image": book.cover_image,
            "publisher": book.publisher,
            "abstract_descript": book.abstract_descript,

            "like_count": book.like_count,
            "top_tags": top_tags_map.get(isbn, []),

            "is_liked": isbn in liked_isbn_set,

            "links": {
                "like_toggle_url": f"/books/{isbn}/likes",
                "read_url": f"/bookviews/{isbn}",
                "purchase_url": book.purchase_link,
            },
        })

    serializer = PopularBookSerializer(results, many=True)
    return Response(
        {
            "message": "많이 읽힌 도서 목록 조회 성공",
            "query": q,
            "items": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST", "DELETE"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def book_library(request, isbn):
    # 1) 책 존재 확인 (Book PK=isbn)
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {"message": "도서를 찾을 수 없습니다.", "error": {"code": "BOOK_NOT_FOUND"}},
            status=status.HTTP_404_NOT_FOUND,
        )

    user = request.user

    # 2) POST: 내 서재 추가
    if request.method == "POST":
        obj, created = Library.objects.get_or_create(user=user, book=book)
        return Response(
            {
                "message": "내 서재에 도서가 추가되었습니다.",
                "library": {
                    "isbn": book.isbn,
                    "is_downloaded": obj.is_downloaded,
                    "book_expiration_date": obj.book_expiration_date,
                    "added_at": obj.added_at,
                },
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # 3) DELETE: 내 서재 삭제
    deleted_count, _ = Library.objects.filter(user=user, book=book).delete()

    if deleted_count == 0:
        return Response(
            {
                "message": "내 서재에 없는 도서입니다.",
                "error": {"code": "LIBRARY_ITEM_NOT_FOUND"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "message": "내 서재에서 도서가 삭제되었습니다.",
            "isbn": book.isbn,
            "in_library": False,
        },
        status=status.HTTP_200_OK,
    )

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def books_search(request):
    """
    현재 검색 대상 필드
    Book.title
    Book.subtitle
    Book.authors_book_list (= Author.name)
    Book.publisher
    """
    query = request.GET.get("q", "").strip()

    if not query:
        return Response(
            {
                "message": "검색어(q)는 필수입니다.",
                "error": {"code": "VALIDATION_ERROR", "field": "q"},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        limit = int(request.GET.get("limit", DEFAULT_LIMIT))
    except ValueError:
        limit = DEFAULT_LIMIT

    limit = min(limit, MAX_LIMIT)

    # 1) 검색 쿼리
    books_qs = (
        Book.objects
        .prefetch_related("authors_book_list__author")
        .filter(
            Q(title__icontains=query) |
            Q(subtitle__icontains=query) |
            Q(publisher__icontains=query) |
            Q(authors_book_list__author__name__icontains=query)
        )
        .distinct()
        .order_by("-like_count", "title")[:limit]
    )

    # 2) 찜 여부 계산
    liked_isbn_set = set()
    if request.user.is_authenticated:
        liked_isbn_set = set(
            UserBookLike.objects
            .filter(user=request.user, book__in=books_qs)
            .values_list("book__isbn", flat=True)
        )

    # 3) 응답 조립
    items = []
    for book in books_qs:
        authors = [
            ab.author.name
            for ab in book.authors_book_list.all()
        ]

        items.append({
            "isbn": book.isbn,
            "title": book.title,
            "authors": authors,
            "publisher": book.publisher,
            "cover_image": book.cover_image,
            "is_liked": book.isbn in liked_isbn_set,
        })

    serializer = BookSearchSerializer(items, many=True)

    return Response(
        {
            "message": "도서 검색 성공",
            "query": query,
            "items": serializer.data,
        },
        status=status.HTTP_200_OK,
    )

# --------------------------
# Bookviews
# --------------------------
def extract_text_from_epub(epub_path: str) -> str:
    book = epub.read_epub(epub_path)

    chunks = []
    for item in book.get_items():
        # 본문 문서만 추출 (ITEM_DOCUMENT)
        # ebooklib에서 문서 타입이 9인 케이스가 일반적
        if item.get_type() == 9:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            if text:
                chunks.append(text)

    return "\n\n".join(chunks)

@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def bookview_content(request, isbn):
    # 1) query params 파싱
    try:
        from_pos = int(request.query_params.get("from", "0"))
        limit = int(request.query_params.get("limit", "1000"))
    except ValueError:
        return error_response("from, limit은 정수여야 합니다.", "INVALID_QUERY", 400)

    if from_pos < 0:
        return error_response("from은 0 이상이어야 합니다.", "INVALID_QUERY", 400)

    # limit 안전장치 (너무 큰 요청 방지)
    if limit <= 0 or limit > 5000:
        return error_response("limit은 1~5000 사이여야 합니다.", "INVALID_QUERY", 400)

    # 2) Book 존재
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return error_response("존재하지 않는 도서입니다.", "BOOK_NOT_FOUND", 404)

    # 3) 권한/만료 체크 (Library 기반)
    try:
        library = Library.objects.get(user=request.user, book=book)
    except Library.DoesNotExist:
        return error_response("읽기 권한이 없습니다.", "NOT_IN_LIBRARY", 403)

    now = timezone.now()
    if library.book_expiration_date and library.book_expiration_date <= now:
        return error_response("열람 기간이 만료되었습니다.", "EXPIRED", 403)

    # 4) epub 파일 경로 결정
    # book.epub_file에 "epubs/978....epub" 같은 상대경로 저장
    epub_rel = book.epub_file  # 현재 필드명 유지 (URLField라도 로컬경로 문자열이 들어있다는 가정)
    epub_path = os.path.join(settings.MEDIA_ROOT, epub_rel)

    if not os.path.exists(epub_path):
        return error_response("EPUB 파일을 찾을 수 없습니다.", "EPUB_NOT_FOUND", 404)

    # 5) epub -> 전체 텍스트
    try:
        full_text = extract_text_from_epub(epub_path)
    except Exception:
        return error_response("EPUB 파싱에 실패했습니다.", "EPUB_PARSE_FAILED", 500)

    total_length = len(full_text)
    if from_pos > total_length:
        return error_response("from이 본문 길이를 초과했습니다.", "OUT_OF_RANGE", 416)

    # 6) 슬라이싱
    end_pos = min(from_pos + limit, total_length)
    content = full_text[from_pos:end_pos]

    has_more = end_pos < total_length
    next_from = end_pos if has_more else None

    # 7) 응답
    return Response(
        {
            "message": "도서 본문 조회 성공",
            "content": {
                "isbn": book.isbn,
                "from": from_pos,
                "limit": limit,
                "to": end_pos,
                "location_unit": "char",
                "total_length": total_length,
                "has_more": has_more,
                "next_from": next_from,
                "text": content,
            },
        },
        status=200,
    )

@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def bookview_meta(request, isbn):
    # 1) Book 존재 확인
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return error_response("존재하지 않는 도서입니다.", "BOOK_NOT_FOUND", 404)

    # 2) 서재(Library) 확인 = 읽기 권한 확인
    try:
        library = Library.objects.get(user=request.user, book=book)
    except Library.DoesNotExist:
        return error_response("읽기 권한이 없습니다.", "NOT_IN_LIBRARY", 403)

    # 3) 만료 체크
    now = timezone.now()
    if library.book_expiration_date is not None and library.book_expiration_date <= now:
        return error_response("열람 기간이 만료되었습니다.", "EXPIRED", 403)

    # 4) 최근 UserBookHistory 1개 가져오기
    # - last_read_at이 null일 수도 있어서 started_at로 보조 정렬
    history = (
        UserBookHistory.objects
        .filter(user=request.user, book=book)
        .order_by("-last_read_at", "-started_at")
        .first()
    )

    # 5) viewer 초기값 구성
    if history and history.current_location is not None:
        initial_location = int(history.current_location)
    else:
        initial_location = 0

    if history:
        progress_percent = float(history.progress_percent or 0.0)
        last_read_at = history.last_read_at.isoformat() if history.last_read_at else None
        started_at = history.started_at.isoformat() if history.started_at else None
        finished_at = history.finished_at.isoformat() if history.finished_at else None
    else:
        progress_percent = 0.0
        last_read_at = None
        started_at = None
        finished_at = None

    # 6) progress_percent 범위 안전 처리(0~100)
    if progress_percent < 0:
        progress_percent = 0.0
    if progress_percent > 100:
        progress_percent = 100.0

    # 7) 응답 (뷰어 초기화 메타)
    return Response(
        {
            "message": "도서 뷰 메타 조회 성공",
            "bookview": {
                "book": {
                    "isbn": book.isbn,
                    "title": book.title,
                    "subtitle": book.subtitle,
                    "publisher": book.publisher,
                    "cover_image": book.cover_image,
                    "lang": book.lang,
                    "page_count": book.page_count,
                    "published_date": book.published_date.isoformat()
                    if book.published_date
                    else None,
                    "toc": book.toc,
                },
                "permission": {
                    "can_read": True,
                    "reason": None,
                },
                "viewer": {
                    "initial_location": initial_location,
                    "location_unit": "char",
                    "progress_percent": progress_percent,
                },
                "reading_state": {
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "last_read_at": last_read_at,
                    "current_location": initial_location,
                },
                "library": {
                    "is_downloaded": library.is_downloaded,
                    "book_expiration_date": library.book_expiration_date.isoformat()
                    if library.book_expiration_date
                    else None,
                    "added_at": library.added_at.isoformat() if library.added_at else None,
                },
                "drm": {
                    "allow_copy": False,
                    "allow_download": False,
                    "allow_screenshot": False,
                },
                "server_time": now.isoformat(),
            },
        },
        status=200,
    )

@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def bookview_progress(request, isbn):
    # 1) 책 존재 확인 (Book pk=isbn)
    try:
        book = Book.objects.get(isbn=isbn)
    except Book.DoesNotExist:
        return Response(
            {
                "message": "도서를 찾을 수 없습니다.",
                "error": {"code": "BOOK_NOT_FOUND"},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2) 요청 값 파싱
    location = request.data.get("location")
    location_unit = request.data.get("location_unit")
    progress_percent = request.data.get("progress_percent")

    # 3) 유효성 검사
    # location
    if location is None:
        return Response(
            {"message": "location은 필수입니다.", "error": {"code": "VALIDATION_ERROR", "field": "location"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        location = int(location)
    except (TypeError, ValueError):
        return Response(
            {"message": "location은 정수여야 합니다.", "error": {"code": "VALIDATION_ERROR", "field": "location"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if location < 0:
        return Response(
            {"message": "location은 0 이상이어야 합니다.", "error": {"code": "VALIDATION_ERROR", "field": "location"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # location_unit
    if not location_unit:
        return Response(
            {"message": "location_unit은 필수입니다.", "error": {"code": "VALIDATION_ERROR", "field": "location_unit"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if location_unit not in ["char", "page", "byte"]:  # TODO: 뷰어 기준으로 허용값 조정 필요
        return Response(
            {"message": "location_unit 값이 올바르지 않습니다.", "error": {"code": "VALIDATION_ERROR", "field": "location_unit"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # progress_percent
    if progress_percent is None:
        return Response(
            {"message": "progress_percent는 필수입니다.", "error": {"code": "VALIDATION_ERROR", "field": "progress_percent"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        progress_percent = int(progress_percent)
    except (TypeError, ValueError):
        return Response(
            {"message": "progress_percent는 정수여야 합니다.", "error": {"code": "VALIDATION_ERROR", "field": "progress_percent"}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if progress_percent < 0 or progress_percent > 100:
        return Response(
            {"message": "progress_percent는 0~100 범위여야 합니다.", "error": {"code": "VALIDATION_ERROR", "field": "progress_percent"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 4) UserBookHistory upsert (없으면 생성, 있으면 업데이트)
    user = request.user
    history, created = UserBookHistory.objects.get_or_create(user=user, book=book)

    # 5) 저장
    history.current_location = location
    history.location_unit = location_unit
    history.progress_percent = progress_percent
    history.last_read_at = timezone.now()
    history.save()

    return Response(
        {
            "message": "읽기 위치가 업데이트되었습니다.",
            "viewer": {
                "isbn": book.isbn,
                "last_location": history.current_location,
                "location_unit": history.location_unit,
                "progress_percent": history.progress_percent,
                "last_read_at": history.last_read_at,
            },
        },
        status=status.HTTP_200_OK,
    )


# --------------------------
# Main
# --------------------------
def _normalize_reading_status_for_user(user, inactive_days=30, min_days_before_stop=3):
    """
    메인 조회 시점에만 실행하는 가벼운 정리 로직(on-demand).
    - READING인데 N일 이상 활동이 없으면 STOPPED로 전환
    - started_at이 너무 최근이면(예: 3일 이내) STOPPED 제외(안전장치)
    """
    now = timezone.now()
    stop_cutoff = now - timedelta(days=inactive_days)
    min_started_cutoff = now - timedelta(days=min_days_before_stop)

    qs = UserBookHistory.objects.filter(user=user, status=UserBookHistory.Status.READING)

    for h in qs:
        # started_at이 너무 최근이면 중단 처리하지 않음
        if h.started_at and h.started_at > min_started_cutoff:
            continue

        # last_read_at이 있으면 last_read_at 기준, 없으면 started_at 기준
        base_time = h.last_read_at or h.started_at

        if base_time and base_time <= stop_cutoff:
            h.status = UserBookHistory.Status.STOPPED
            h.save(update_fields=["status", "updated_at"])


@api_view(["GET"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated, IsActiveUser])
def main_current_reading(request):
    try:
        # 1) 오래된 READING 정리 (정합성 확보)
        _normalize_reading_status_for_user(
            request.user,
            inactive_days=30,        # 정책값: 30일 미접속/미열람이면 중단 처리
            min_days_before_stop=3,  # 안전장치: 시작한지 3일 이내는 중단 제외
        )

        # 2) 지금 읽는 책 선정: last_read_at 최신 1권, 동률이면 started_at
        history = (
            UserBookHistory.objects
            .select_related("book")
            .filter(user=request.user, status=UserBookHistory.Status.READING)
            .order_by("-last_read_at", "-started_at", "-id")
            .first()
        )

        # 3) 없으면 200 + null
        if history is None:
            return Response(
                {
                    "message": "지금 읽는 책이 없습니다.",
                    "current_reading_book": None,
                },
                status=status.HTTP_200_OK,
            )

        serializer = CurrentReadingBookSerializer(history)
        return Response(
            {
                "message": "지금 읽는 책 조회 성공",
                "current_reading_book": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
    
    except Exception:
        return Response(
            {
                "message": "서버 오류가 발생했습니다.",
                "error": {"code": "INTERNAL_SERVER_ERROR"},
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def main_banner(request):
    # order 기준 정렬 + 상위 N개만 반환
    banners = sorted(MAIN_BANNERS, key=lambda x: x.get("order", 999))[:BANNER_LIMIT]

    return Response(
        {
            "message": "메인 배너 조회 성공",
            "banners": banners,
        },
        status=status.HTTP_200_OK,
    )

# --------------------------
# allauth with JWT
# --------------------------
@permission_classes([IsAuthenticated])
@api_view(["POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
def jwt_exchange(request):
    refresh = RefreshToken.for_user(request.user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    })





