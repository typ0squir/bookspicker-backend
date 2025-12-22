from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    sex = models.CharField(max_length=10, blank=True, null=True)
    birth_year = models.CharField(max_length=4, blank=True, null=True)

    books_per_month = models.PositiveIntegerField(blank=True, null=True)
    profile_image = models.URLField(blank=True, null=True)
    is_profile_public = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    resigned_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_coldstart_completed(self):
        """
        콜드스타트(온보딩) 완료 여부 확인
        - nickname 존재 여부
        - Trait의 coldstart_tags_done_at, coldstart_books_done_at 존재 여부
        """
        # Trait 존재 여부 확인
        if not hasattr(self, 'trait'):
            return False
            
        trait = self.trait
        return all([
            self.nickname,
            trait.coldstart_tags_done_at,
            trait.coldstart_books_done_at
        ])

class Trait(models.Model):
    """
    사용자 성향 정보
    - coldstart_tags: 최초 1회, 사용자가 직접 선택한 관심 태그 (보존)
    - interesting_tags: 사용자 활동 기반으로 시스템이 계산한 현재 관심 태그 (교체 가능)
    - vector: AI로 계산되는 사용자 성향 벡터
    """

    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="trait",
    )

    # 콜드스타트 (1회 입력, 수정 불가)
    coldstart_tags = models.ManyToManyField(
        "api.Tag",
        blank=True,
        related_name="coldstart_traits",
    )
    coldstart_tags_done_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    coldstart_books = models.ManyToManyField(
        "api.Book",
        blank=True,
        related_name="interesting_traits",
    )
    coldstart_books_done_at = models.DateTimeField(null=True, blank=True)

    # 활동 기반 현재 관심 태그 (배치로 주기적 교체)
    interesting_tags = models.ManyToManyField(
        "api.Tag",
        blank=True,
        related_name="interesting_tags",
    )
    interesting_tags_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    interesting_books = models.ManyToManyField(
        "api.Book",
        blank=True,
        related_name="interesting_books",
    )
    interesting_books_updated_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # AI 계산 성향 벡터
    vector = models.JSONField(
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Trait of user {self.user_id}"