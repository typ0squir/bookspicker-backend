from django.db import models
from django.conf import settings

# -----------------------------
# Book
# -----------------------------
class Book(models.Model):
    isbn = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, null=True)
    genre = models.CharField(max_length=100)
    publisher = models.CharField(max_length=100)
    one_line_desc = models.TextField()
    two_line_desc = models.TextField()
    full_desc = models.TextField()
    cover = models.CharField(max_length=500)               # 이미지 URL
    readed_num_month = models.IntegerField(default=0)
    readed_num_week = models.IntegerField(default=0)
    is_steady = models.BooleanField(default=False)
    published_date = models.DateTimeField()
    page_count = models.IntegerField(default=0)
    series = models.CharField(max_length=100, null=True)
    lang = models.CharField(max_length=50)
    like_num = models.IntegerField(default=0)
    toc = models.JSONField(null=True, blank=True)
    content = models.CharField(max_length=500)  # epub 파일 주소


# -----------------------------
# 사용자 성향(Trait)
# -----------------------------
class Trait(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    vector = models.JSONField(null=True, blank=True)    # 8차원 벡터 등


# -----------------------------
# Tag
# -----------------------------
class Tag(models.Model):
    content = models.CharField(max_length=50)


# -----------------------------
# Book - Tag (N:N)
# -----------------------------
class BookTag(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    click_num = models.IntegerField(default=0)


# -----------------------------
# Highlight (독서 하이라이트)
# -----------------------------
class Highlight(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    isbn = models.IntegerField()
    content = models.TextField()
    created_at = models.DateTimeField()
    location_start = models.IntegerField()
    location_end = models.IntegerField()


# -----------------------------
# Library (내 서재)
# -----------------------------
class Library(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    isbn = models.IntegerField()
    is_downloaded = models.BooleanField(default=False)
    book_verification = models.DateTimeField(null=True)
    added_at = models.DateTimeField()


# -----------------------------
# Wishlist (찜 목록)
# -----------------------------
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    isbn = models.IntegerField()
    added_at = models.DateTimeField()


# -----------------------------
# 독서 이력(user_book_history)
# -----------------------------
class UserBookHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    isbn = models.IntegerField()

    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(null=True)
    last_page = models.IntegerField(default=0)
    last_read_at = models.DateTimeField(null=True)
    progress = models.FloatField(default=0)                 # %
    review = models.CharField(max_length=280, null=True)
    like = models.BooleanField(default=False)


# -----------------------------
# Author
# -----------------------------
class Author(models.Model):
    author_name = models.CharField(max_length=100)
    introduction = models.TextField()


# -----------------------------
# Author - Book (N:N)
# -----------------------------
class AuthorsBook(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)   # 예: 저자 / 역자
