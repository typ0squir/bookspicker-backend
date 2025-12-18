from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

# --------------------------
# Author / AuthorsBook
# --------------------------
class Author(models.Model):
    name = models.CharField(max_length=100)
    profile_image = models.URLField(blank=True, null=True)
    bio = models.TextField()

    def __str__(self):
        return self.name

class AuthorRole(models.TextChoices):
    AUTHOR = "AUTHOR", "지은이"
    TRANSLATOR = "TRANSLATOR", "옮긴이"
    EDITOR = "EDITOR", "엮은이"
    ILLUSTRATOR = "ILLUSTRATOR", "그림"
    ETC = "ETC", "기타"

class AuthorsBook(models.Model):
    author = models.ForeignKey(
        "Author",
        on_delete=models.CASCADE,
        related_name="authors_book_list"
    )
    book = models.ForeignKey(
        "Book",
        on_delete=models.CASCADE,
        related_name="authors_book_list"
    )

    role = models.CharField(
        max_length=20,
        choices=AuthorRole.choices,
        default=AuthorRole.AUTHOR
    )

    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ("author", "book", "role")
        # 같은 작가(author)가 같은 책(book)에 같은 역할(role)로 두 번 이상 등록 불가


# --------------------------
# Genre, Book (통계 필드 포함)
# --------------------------
class GenreParent(models.Model):
    name = models.CharField(max_length=100, unique=True)

class GenreChild(models.Model):
    parent = models.ForeignKey(
        GenreParent,
        on_delete=models.CASCADE,
        related_name="children",
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.parent.name} > {self.name}"
    
class Book(models.Model):
    isbn = models.CharField(primary_key=True, max_length=13)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, null=True)
    publisher = models.CharField(max_length=100)

    one_line_descript = models.CharField(max_length=255)
    two_line_descript = models.CharField(max_length=500)
    full_descript = models.TextField()

    cover_image = models.URLField()
    epub_file = models.URLField()

    published_date = models.DateField()
    page_count = models.PositiveIntegerField()
    series_name = models.CharField(max_length=100, blank=True, null=True)
    lang = models.CharField(max_length=20)

    top_tags = models.JSONField(default=list, blank=True)
    top_tags_updated_at = models.DateTimeField(null=True, blank=True)

    # ===== 집계 필드 (배치로 갱신) =====
    readed_num_week = models.PositiveIntegerField(default=0)
    readed_num_month = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    is_steady = models.BooleanField(default=False)

    toc = models.JSONField()
    purchase_link = models.URLField(blank=True, null=True)

    genre = models.ForeignKey(
        GenreChild,
        on_delete=models.SET_NULL,
        null=True,
        related_name="book_list",
    )   # on_delete=models.SET_NULL -> 장르가 사라져도 책은 사라지면 안 되기 때문

    def __str__(self):
        return self.title


# --------------------------
# Tag / BookTag
# --------------------------

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    global_count = models.PositiveIntegerField(default=0)  # 전체 누적

    normalized = models.CharField(max_length=50, db_index=True)
    status = models.CharField(
        max_length=20,
        default="ACTIVE",
        choices=[("ACTIVE","ACTIVE"), ("BLOCKED","BLOCKED"), ("MERGED","MERGED")]
    )

    canonical = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="aliases"
    )

class BookTag(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="book_tag_list"
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="book_tag_list"
    )
     # ===== 집계 필드 =====
    base_count = models.PositiveIntegerField(default=0)   # 기본 태그 가중치 (ex. 30)
    user_count = models.PositiveIntegerField(default=0)   # 사용자 기여 누적
    tag_count = models.PositiveIntegerField(default=0)    # base + user (노출 기준)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("book", "tag")


# --------------------------
# Library / Wishlist / Like
# --------------------------
class Library(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="library_list"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="library_list"
    )
    is_downloaded = models.BooleanField(default=False)
    book_expiration_date = models.DateTimeField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")

class Wishlist(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="wishlist_list"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="wishlist_list"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")

class UserBookLike(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_book_like_list"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="user_book_like_list"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "book")


# --------------------------
# UserBookHistory (통계 원천)
# --------------------------
class UserBookHistory(models.Model):
    class Status(models.TextChoices):
        READING = "READING", "읽는 중"
        FINISHED = "FINISHED", "완독"
        STOPPED = "STOPPED", "중단" # 중도 이탈 상태

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_book_history"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="user_book_history"
    )

    started_at = models.DateTimeField() # 읽기 시작
    last_read_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.READING)
    progress_percent = models.FloatField(default=0.0)
    current_location = models.PositiveIntegerField(blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    # 레코드 관리용
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "status", "-last_read_at"]),
        ]

# --------------------------
# Highlight
# --------------------------
class Highlight(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="highlight_list"
    )
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="highlight_list"
    )

    content = models.TextField()
    start_page = models.PositiveIntegerField()
    end_page = models.PositiveIntegerField()
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)



