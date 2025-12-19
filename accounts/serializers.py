from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ColdStartNicknameSerializer(serializers.Serializer):
    nickname = serializers.CharField()

    def validate_nickname(self, value):
        # 길이 검사
        if len(value) < 2 or len(value) > 20:
            raise serializers.ValidationError("닉네임은 2~20자여야 합니다.")

        # 문자 검사
        for ch in value:
            if not (ch.isalnum() or ch == "_"):
                raise serializers.ValidationError(
                    "닉네임은 영문, 숫자, 언더바(_)만 가능합니다."
                )

        # 중복 검사 (가장 기본)
        if User.objects.filter(nickname=value).exists():
            raise serializers.ValidationError("이미 존재하는 닉네임입니다. 다른 닉네임을 사용해주세요.")

        return value

class ColdStartTagsSerializer(serializers.Serializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False
    )

class ColdStartBooksSerializer(serializers.Serializer):
    isbn_list = serializers.ListField(
        child=serializers.CharField(max_length=13),
        allow_empty=False,
    )

class AccountHighlightListSerializer(serializers.Serializer):
    highlight_id = serializers.IntegerField()
    isbn = serializers.CharField()
    book_title = serializers.CharField()
    cover_image = serializers.CharField(allow_null=True, required=False)

    # 하이라이트 좌표/진행 관련
    start_location = serializers.IntegerField()
    end_location = serializers.IntegerField()

    # 하이라이트 본문
    content = serializers.CharField(allow_blank=True, required=False)
    created_at = serializers.DateTimeField()