from rest_framework import serializers
from datetime import date
from django.contrib.auth import get_user_model

User = get_user_model()


# --------------------------
# ColdStart
# --------------------------
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

class ColdStartProfileInfoInnerSerializer(serializers.Serializer):
    
    birth_year = serializers.IntegerField(required=False)
    sex = serializers.CharField(required=False)
    books_per_month = serializers.IntegerField(required=False)

    def validate_birth_year(self, value):
        # 현실적인 범위로 제한
        if value < 1900 or value > date.today().year:
            raise serializers.ValidationError("birth_year 범위가 올바르지 않습니다.")
        return value

    def validate_sex(self, value):
        v = str(value).strip().upper()
        allowed = ["F", "M", "N"]
        if v not in allowed:
            raise serializers.ValidationError("sex는 F/M/N 중 하나여야 합니다.")
        return v

    def validate_books_per_month(self, value):
        if value < 0 or value > 300:
            raise serializers.ValidationError("books_per_month 범위가 올바르지 않습니다.")
        return value


class ColdStartProfileInfoRequestSerializer(serializers.Serializer):
    profile_info = ColdStartProfileInfoInnerSerializer()


# --------------------------
# Log
# --------------------------
class AccountCommentListItemSerializer(serializers.Serializer):
    comment_id = serializers.IntegerField()  # = UserBookHistory.id
    isbn = serializers.CharField()

    content = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()

    status = serializers.CharField()
    progress_percent = serializers.FloatField()

    book = serializers.DictField()

# --------------------------
# Personal Info
# --------------------------
class NicknameUpdateSerializer(serializers.Serializer):
    nickname = serializers.CharField()

    def validate_nickname(self, value):
        nickname = value.strip()

        if nickname == "":
            raise serializers.ValidationError("nickname은 비어있을 수 없습니다.")

        if len(nickname) < 2 or len(nickname) > 20:
            raise serializers.ValidationError("nickname은 2~20자여야 합니다.")

        # 중복 검사 (본인 제외)
        request = self.context.get("request")
        user = getattr(request, "user", None)

        qs = User.objects.filter(nickname=nickname)
        if user and user.is_authenticated:
            qs = qs.exclude(id=user.id)

        if qs.exists():
            raise serializers.ValidationError("이미 사용 중인 nickname입니다.")

        return nickname