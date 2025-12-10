from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    사용자 정보
    """
    nickname = models.CharField(max_length=30, blank=True, null=True)   # 닉네임
    email = models.EmailField(max_length=100, unique=True)              # 이메일
    sex = models.CharField(max_length=10, blank=True, null=True)        # 성별
    books_per_month = models.IntegerField(default=0)                    # 한 달간 독서량
    birth_year = models.DateField(blank=True, null=True)                # 생년 (연도만 쓰고 싶으면 IntegerField로 바꿔도 됨)
    profile_pic = models.URLField(max_length=500, blank=True, null=True)  # 프로필 사진 경로/URL
    is_profile_public = models.BooleanField(default=True)               # 프로필 공개 여부

    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.nickname or self.username or self.email


class Trait(models.Model):
    """
    사용자 성향 정보
    """
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="trait",
    )                                   # 사용자 고유 ID
    vector = models.JSONField()         # 사용자 성향 벡터

    def __str__(self):
        return f"Trait of {self.user_id}"