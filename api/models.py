from django.db import models
from django.conf import settings


# -----------------------------
# Tag
# -----------------------------
class Tag(models.Model):
    """
    태그 정보
    """
    name = models.CharField(max_length=100, unique=True)  # 내용

    def __str__(self):
        return self.name


# -----------------------------
# Book
# -----------------------------
class Book(models.Model):
    """
    책 정보
    """
    isbn = models.BigIntegerField(primary_key=True)          # 책 고유 번호(ISBN)
    title = models.CharField(max_length=200)                 # 제목
    subtitle = models.CharField(max_length=200, blank=True, null=True)  # 부제목
    genre = models.CharField(max_length=100)                 # 장르
    publisher = models.CharField(max_length=100)             # 출판사

    one_line_descript = models.TextField()                   # 한 줄 소개
    two_line_descript = models.TextField()                   # 두 줄 소개
    full_descript = models.TextField()                       # 소개(전체)

    cover_image = models.URLField(max_length=500)                  # 표지 url
    readed_num_month = models.IntegerField(default=0)        # 한달 간 읽힌 횟수
    readed_num_week = models.IntegerField(default=0)         # 일주일 간 읽힌 횟수
    is_steady = models.BooleanField(default=False)           # 스테디 셀러 여부

    published_date = models.DateTimeField()                  # 출간일자
    page_count = models.IntegerField(default=0)              # 페이지 수
    series = models.CharField(max_length=100, blank=True, null=True)  # 시리즈 명
    lang = models.CharField(max_length=50)                   # 언어
    like_count = models.IntegerField(default=0)                # 좋아요 수

    toc = models.JSONField(blank=True, null=True)            # 목차 JSON
    epub_file = models.CharField(max_length=500, blank=True, null=True)  # epub 파일 경로
    purchase_link = models.TextField(blank=True, null=True)  # 책 구매 주소

    def __str__(self):
        return f"{self.title} ({self.isbn})"


# -----------------------------
# Author & AuthorsBook
# -----------------------------
class Author(models.Model):
    """
    작가 정보
    """
    author_name = models.CharField(max_length=100)   # 이름
    introduction = models.TextField(blank=True, null=True)  # 소개

    def __str__(self):
        return self.author_name


class AuthorsBook(models.Model):
    """
    작가 - 책 (N:M) + 역할
    """

    # 예: 'author', 'translator' 등 자유 텍스트
    role = models.CharField(max_length=50)         # 역할
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="author_books",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="book_authors",
    )

    class Meta:
        db_table = "authors_book"
        unique_together = ("author", "book", "role")

    def __str__(self):
        return f"{self.author} - {self.book} ({self.role})"


# -----------------------------
# BookTag (Book - Tag N:M)
# -----------------------------
class BookTag(models.Model):
    """
    책 - 태그 정보
    """
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="book_tags",
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="tag_books",
    )
    tag_count = models.IntegerField(
        default=0,
        help_text="이 책에 대해 해당 태그가 누적해서 선택된 횟수",
    )

    class Meta:
        db_table = "book_tag"
        unique_together = ("book", "tag")

    def __str__(self):
        return f"{self.book_id} - {self.tag_id}"


# -----------------------------
# Highlight
# -----------------------------
class Highlight(models.Model):
    """
    사용자가 밑줄/하이라이트 한 문장
    """
    content = models.TextField()                            # 내용
    start_page = models.IntegerField()                      # 시작 페이지
    end_page = models.IntegerField()                        # 끝 페이지
    start_offset = models.IntegerField()                    # 시작 오프셋
    end_offset = models.IntegerField()                      # 끝 오프셋
    created_at = models.DateTimeField(auto_now_add=True)    # 만들어진 날짜

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="highlights",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="highlights",
    )

    def __str__(self):
        return f"Highlight #{self.id} by {self.user_id} on {self.book_id}"


# -----------------------------
# Library (서재 책 목록 정보)
# -----------------------------
class Library(models.Model):
    """
    서재 책 목록 정보
    """
    is_downloaded = models.BooleanField(default=False)      # 다운로드 여부
    book_verification = models.DateTimeField(blank=True, null=True)  # 다운로드 인증 날짜
    added_at = models.DateTimeField(auto_now_add=True)      # 목록에 추가된 날짜

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="libraries",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="in_libraries",
    )

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user_id} - {self.book_id}"


# -----------------------------
# Wishlist (찜한 책 목록)
# -----------------------------
class Wishlist(models.Model):
    """
    찜한 책 목록
    """
    added_at = models.DateTimeField(auto_now_add=True)  # 목록에 추가된 날짜

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="in_wishlists",
    )

    class Meta:
        unique_together = ("user", "book")

    def __str__(self):
        return f"Wishlist {self.user_id} - {self.book_id}"


# -----------------------------
# UserBookHistory (독서 이력 정보)
# -----------------------------
class UserBookHistory(models.Model):
    """
    독서 이력 정보
    """
    started_at = models.DateTimeField()                     # 읽기 시작한 날짜
    finished_at = models.DateTimeField(blank=True, null=True)  # 모두 읽은 날짜
    last_page = models.IntegerField(blank=True, null=True)      # 마지막으로 읽은 페이지
    review = models.CharField(max_length=200, blank=True, null=True)  # 짧은 리뷰/코멘트
    like = models.BooleanField(default=False)               # 좋아요 누른 여부
    last_read_at = models.DateTimeField(blank=True, null=True)  # 마지막으로 읽은 날짜
    progress = models.FloatField(default=0.0)               # 진행률

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reading_histories",
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="reading_histories",
    )

    def __str__(self):
        return f"History #{self.id} - {self.user_id} - {self.book_id}"
    

# -----------------------------
# Review
# -----------------------------
class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")

    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 리뷰가 어떤 태그를 선택했는지 기록
    tags = models.ManyToManyField(Tag, through="ReviewTag", related_name='reviews', blank=True,)

    def __str__(self):
        return f"Review {self.id} - {self.book_id} by {self.user_id}"

class ReviewTag(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("review", "tag")

    def __str__(self):
        return f"{self.review_id} - {self.tag_id}"
    











    
