from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone

from .serializers import (
    ColdStartNicknameSerializer,
    ColdStartTagsSerializer,
    ColdStartBooksSerializer,
)

from api.models import Tag, Book
from .models import Trait

def err(message, code, http_status):
    return Response(
        {"message": message},
        status=http_status
    )


@api_view(["POST"])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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

