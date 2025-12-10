from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from django.db.models import Q, F
from rest_framework import status

from api.models import (
    Book, Review, ReviewTag, Tag, BookTag, UserBookHistory
)
from .serializers import (
    BookListSerializer, 
    BookDetailSerializer, 
    BookPopularSerializer, 
    BookSearchSerializer,
    ReviewCreateSerializer,
    ReviewResponseSerializer,
    ReviewSerializer,
)


@api_view(['GET'])
def book_list(request):
    books = Book.objects.all()
    serializer = BookListSerializer(books, many=True)
    return Response({"books": serializer.data})

@api_view(['GET'])
def book_detail(request, isbn):
    """
    도서 상세 정보 조회 API
    GET /api/books/<isbn>/
    """
    book = get_object_or_404(Book, pk=isbn)
    base_data = BookDetailSerializer(book).data

    # TODO: 아래 값들은 현재 더미이며, 나중에 실제 DB/로직으로 교체 예정
    authors = ["한윤섭(지은이)", "이로우(그림)"]
    is_liked = True  # TODO: 로그인 사용자 + Wishlist/Like 모델과 연동
    action_urls = {
        "read_now_url": f"https://example.com/reader/{book.isbn}",
        "wish_url": f"https://example.com/users/wish/{book.isbn}",
        "purchase_url": book.purchase_link or f"https://example.com/store/{book.isbn}",
    }
    why_picked = {
        "body": (
            "최근 닉네임님이 고른 책들을 보면, 사람 사이의 따뜻함과 조용한 연민이 스며든 이야기들을 자주 선택하시는 느낌이었어요. "
            "『이야기의 신』은 그런 닉네임님의 취향과 닿아 있는 동화 같은 장편이에요. "
            "어른이 되었지만 여전히 마음 한구석에 남아 있는 불안과 따뜻함을 동시에 건드려 주는 이야기라 올해 추천 도서로 선택했어요."
        )
    }
    tags = [
        {"id": 1, "name": "따뜻한 이야기", "tag_count": 128},
        {"id": 2, "name": "성장", "tag_count": 8},
        {"id": 3, "name": "가족", "tag_count": 148},
    ]
    author_intro = (
        "한윤섭 작가는 국내 문학에서 오랫동안 활약해 온 이야기꾼이며, "
        "이로우 작가는 감각적인 그림으로 독자에게 깊은 인상을 남기는 일러스트레이터이다."
    )
    comments = [
        {
            "comment_id": 101,
            "user": {
                "nickname": "행인1",
                "profile_image": "https://example.com/users/1/profile.png",
            },
            "created_at": "2025-02-01T21:15:00",
            "content": "마지막 장을 덮고 한참 동안 여운이 남는 책이었어요.",
            "is_owner": False,
        },
        {
            "comment_id": 102,
            "user": {
                "nickname": "책읽는고양이",
                "profile_image": "https://example.com/users/2/profile.png",
            },
            "created_at": "2025-02-03T10:02:00",
            "content": "동화처럼 읽히는데 메시지는 결코 가볍지 않아요.",
            "is_owner": True,
        },
    ]
    comment_count = len(comments)

    book_payload = {
        **base_data,
        "authors": authors,
        "is_liked": is_liked,
        "action_urls": action_urls,
        "why_picked": why_picked,
        "tags": tags,
        "author_intro": author_intro,
        "comments": comments,
        "comment_count": comment_count,
    }

    response_data = {
        "message": "도서 상세 정보 조회 성공",
        "book": book_payload,
    }

    return Response(response_data)

@api_view(['GET'])
def popular_books(request):
    """
    많이 읽힌 도서 목록 조회 API
    GET /api/books/popular/?q=monthly  (or weekly, steady)
    """
    query = request.query_params.get("q", "monthly")

    # 기본 쿼리셋
    qs = Book.objects.all()

    if query == "weekly":
        qs = qs.order_by("-readed_num_week")
        type_label = "weekly"
    elif query == "steady":
        qs = qs.filter(is_steady=True).order_by("-readed_num_month")
        type_label = "steady"
    else:
        # 그 외 값이 들어와도 monthly로 처리
        qs = qs.order_by("-readed_num_month")
        type_label = "monthly"

    # 상위 N권만 제공 (예: 20권)
    qs = qs[:20]

    serializer = BookPopularSerializer(qs, many=True)
    books_data = serializer.data

    # rank 부여 (1부터 시작)
    for idx, item in enumerate(books_data, start=1):
        item["rank"] = idx

    response_data = {
        "message": "많이 읽힌 도서 목록 조회 성공",
        "type": type_label,
        "books": books_data,
        "total": len(books_data),
    }

    return Response(response_data)

@api_view(['GET'])
def search_books(request):
    """
    도서 검색 API
    GET /api/books/search/?q=여행
    """
    query = request.query_params.get("q", "").strip()

    if not query:
        return Response({
            "message": "검색어(q)는 필수입니다.",
            "q": "",
            "books": [],
            "total": 0
        }, status=400)

    # 검색 로직 (title, subtitle, publisher, genre 포함)
    # TODO: 추후에 tag 검색까지 포함하기
    books = Book.objects.filter(
        Q(title__icontains=query) |
        Q(subtitle__icontains=query) |
        Q(publisher__icontains=query) |
        Q(genre__icontains=query)
    ).distinct()

    serializer = BookSearchSerializer(books, many=True)

    return Response({
        "message": "도서 검색 조회 성공",
        "q": query,
        "books": serializer.data,
        "total": len(serializer.data)
    }) 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, isbn):
    book = get_object_or_404(Book, isbn=isbn)
    
    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    content = serializer.validated_data["content"]
    tag_names = serializer.validated_data.get("tags", [])

    # 1) 리뷰 생성
    review = Review.objects.create(
        book=book,
        user=request.user,
        content=content
    )

    # 2) 태그 처리 (기존 태그는 그대로 사용, 없는 태그는 생성)
    for tag_name in tag_names:
        tag_name = tag_name.strip()
        if not tag_name:
            continue

        # a. 태그 생성/재사용
        tag_obj, _ = Tag.objects.get_or_create(name=tag_name)

        # b. 리뷰–태그 연결 (ReviewTag)
        ReviewTag.objects.get_or_create(review=review, tag=tag_obj)

        # c. 책–태그 집계 (BookTag.tag_count 증가)
        book_tag, created = BookTag.objects.get_or_create(
            book=book,
            tag=tag_obj,
            defaults={"tag_count": 0},
        )
        if created:
            # 첫 번째로 선택된 경우
            book_tag.tag_count = 1
            book_tag.save(update_fields=["tag_count"])
        else:
            # 이미 있으면 +1
            BookTag.objects.filter(pk=book_tag.pk).update(
                tag_count=F("tag_count") + 1
            )
    # 3) 응답 직렬화
    response_data = ReviewResponseSerializer(
        review,
        context={"request": request}
    ).data

    return Response({
        "message": "도서 리뷰가 성공적으로 등록되었습니다.",
        "review": response_data,
    })

@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def review_detail(request, isbn, review_id):

    book = get_object_or_404(Book, isbn=isbn)
    review = get_object_or_404(Review, id=review_id, book=book)

    # 권한 체크
    if request.method in ['PATCH', 'DELETE'] and review.user != request.user:
        return Response(
            {"detail": "리뷰를 수정/삭제할 권한이 없습니다."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # GET
    if request.method == 'GET':
        serializer = ReviewSerializer(review, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # PATCH
    if request.method == 'PATCH':
        serializer = ReviewSerializer(
            review,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "도서 리뷰가 수정되었습니다.",
                "review": serializer.data,
            },
            status=status.HTTP_200_OK
        )

    # DELETE
    if request.method == 'DELETE':
        review_tags = ReviewTag.objects.filter(review=review).select_related("tag")

        for rt in review_tags:
            book_tag = BookTag.objects.filter(book=book, tag=rt.tag).first()
            if book_tag:
                BookTag.objects.filter(pk=book_tag.pk).update(
                    tag_count=F("tag_count") - 1
                )

        review_tags.delete()
        review.delete()

        return Response(
            {"message": "도서 리뷰가 성공적으로 삭제되었습니다."},
            status=status.HTTP_200_OK
        )
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def book_like_toggle(request, isbn):
    user = request.user
    book = get_object_or_404(Book, isbn=isbn)

    # 해당 유저의 책 기록 가져오기 or 생성
    history, created = UserBookHistory.objects.get_or_create(
        user=user,
        book=book,
        defaults={"like": True},  # 최초 생성 시 좋아요된 상태로
    )

    # 방금 생성된 경우 → 좋아요 새로 등록
    if created:
        book.like_count += 1
        book.save(update_fields=["like_count"])

        return Response(
            {
                "message": "좋아요가 등록되었습니다.",
                "is_liked": True,
                "like_count": book.like_count,
            },
            status=status.HTTP_201_CREATED,
        )

    # 이미 기록이 있는 경우 → 토글
    if history.like:
        # 좋아요 취소
        history.like = False
        history.save(update_fields=["like"])

        book.like_count -= 1
        book.save(update_fields=["like_count"])

        return Response(
            {
                "message": "좋아요가 취소되었습니다.",
                "is_liked": False,
                "like_count": book.like_count,
            },
            status=status.HTTP_200_OK,
        )
    else:
        # 좋아요 등록
        history.like = True
        history.save(update_fields=["like"])

        book.like_count += 1
        book.save(update_fields=["like_count"])

        return Response(
            {
                "message": "좋아요가 등록되었습니다.",
                "is_liked": True,
                "like_count": book.like_count,
            },
            status=status.HTTP_201_CREATED,
        )


















