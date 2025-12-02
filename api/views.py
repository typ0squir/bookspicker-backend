from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from .models import Book, Library, Wishlist, Highlight, UserBookHistory
from .serializers import (
    BookSerializer, LibrarySerializer, WishlistSerializer,
    HighlightSerializer, UserBookHistorySerializer
)

# -----------------------------
# Books
# -----------------------------
@extend_schema(
    summary="도서 목록 조회",
    description="도서 목록을 조회합니다. 검색 및 장르 필터링이 가능합니다.",
    parameters=[
        OpenApiParameter(name='search', description='제목, 저자, 장르 검색', required=False, type=str),
        OpenApiParameter(name='genre', description='장르 필터', required=False, type=str),
        OpenApiParameter(name='page', description='페이지 번호', required=False, type=int),
    ]
)
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'authorsbook__author__author_name', 'genre']

    def get_queryset(self):
        queryset = super().get_queryset()
        genre = self.request.query_params.get('genre')
        if genre:
            queryset = queryset.filter(genre=genre)
        return queryset

@extend_schema(summary="도서 상세 조회", description="ISBN을 이용하여 도서의 상세 정보를 조회합니다.")
class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'isbn'

# -----------------------------
# Library
# -----------------------------
class LibraryListView(generics.ListCreateAPIView):
    serializer_class = LibrarySerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="내 서재 목록 조회", description="사용자의 서재에 담긴 도서 목록을 조회합니다.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="내 서재에 책 추가", description="ISBN을 이용하여 내 서재에 책을 추가합니다.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Library.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # isbn is passed in body, we need to validate it exists in Books
        isbn = self.request.data.get('isbn')
        get_object_or_404(Book, isbn=isbn)
        # Check if already exists
        if Library.objects.filter(user=self.request.user, isbn=isbn).exists():
            return # Or raise error, but serializer might handle unique together if set
        serializer.save(user=self.request.user, isbn=isbn)

class LibraryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="내 서재에서 책 삭제", description="ISBN을 이용하여 내 서재에서 책을 삭제합니다.")
    def delete(self, request, isbn):
        library_item = get_object_or_404(Library, user=request.user, isbn=isbn)
        library_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class BookDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="책 다운로드 (EPUB)",
        description="내 서재에 있는 책을 다운로드합니다.",
        responses={200: OpenApiResponse(description="File download or URL")}
    )
    def get(self, request, isbn):
        # Check if user owns the book in library
        library_item = get_object_or_404(Library, user=request.user, isbn=isbn)
        book = get_object_or_404(Book, isbn=isbn)
        
        # Assuming content is a URL or file path
        # If it's a URL, return it
        if book.content.startswith('http'):
             return Response({'download_url': book.content})
        
        # If it's a local file path, serve it (simplified)
        # In production, use X-Sendfile or similar
        try:
            return FileResponse(open(book.content, 'rb'))
        except FileNotFoundError:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

# -----------------------------
# Wishlist
# -----------------------------
class WishlistListView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="찜 목록 조회", description="사용자의 찜 목록을 조회합니다.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="찜 목록에 추가", description="ISBN을 이용하여 찜 목록에 책을 추가합니다.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        isbn = self.request.data.get('isbn')
        get_object_or_404(Book, isbn=isbn)
        if Wishlist.objects.filter(user=self.request.user, isbn=isbn).exists():
            return
        serializer.save(user=self.request.user, isbn=isbn)

class WishlistDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="찜 목록에서 삭제", description="ISBN을 이용하여 찜 목록에서 책을 삭제합니다.")
    def delete(self, request, isbn):
        wishlist_item = get_object_or_404(Wishlist, user=request.user, isbn=isbn)
        wishlist_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# -----------------------------
# Highlights
# -----------------------------
class HighlightListView(generics.ListCreateAPIView):
    serializer_class = HighlightSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="하이라이트 목록 조회",
        description="사용자의 하이라이트 목록을 조회합니다. ISBN으로 필터링 가능합니다.",
        parameters=[OpenApiParameter(name='isbn', description='ISBN 필터', required=False, type=int)]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="하이라이트 생성", description="책의 특정 부분에 하이라이트를 생성합니다.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Highlight.objects.filter(user=self.request.user)
        isbn = self.request.query_params.get('isbn')
        if isbn:
            queryset = queryset.filter(isbn=isbn)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class HighlightDetailView(generics.DestroyAPIView):
    queryset = Highlight.objects.all()
    serializer_class = HighlightSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="하이라이트 삭제", description="하이라이트 ID를 이용하여 삭제합니다.")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return Highlight.objects.filter(user=self.request.user)

# -----------------------------
# Reading History
# -----------------------------
class HistoryListView(generics.ListCreateAPIView):
    serializer_class = UserBookHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="독서 기록 조회", description="사용자의 모든 독서 기록을 조회합니다.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="독서 시작 (기록 생성)", description="책 읽기를 시작하여 독서 기록을 생성합니다.")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        return UserBookHistory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        isbn = self.request.data.get('isbn')
        get_object_or_404(Book, isbn=isbn)
        serializer.save(user=self.request.user, isbn=isbn)

class HistoryDetailView(generics.UpdateAPIView):
    serializer_class = UserBookHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'isbn'

    @extend_schema(summary="독서 진행상황/리뷰 업데이트", description="독서 진행률, 마지막 읽은 페이지, 리뷰 등을 업데이트합니다.")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="독서 기록 전체 수정 (PUT)", description="독서 기록을 전체 수정합니다.", exclude=True)
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def get_queryset(self):
        return UserBookHistory.objects.filter(user=self.request.user)

# -----------------------------
# Recommendations
# -----------------------------
class RecommendationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="사용자 맞춤 추천 도서",
        description="사용자의 취향에 맞는 도서를 추천합니다.",
        responses={200: BookSerializer(many=True)}
    )
    def get(self, request):
        # Placeholder for recommendation logic
        # For now, return random 5 books or top rated
        books = Book.objects.order_by('-like_num')[:5]
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

# -----------------------------
# 현재 로그인한 내 정보/토큰 주는 API
# -----------------------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "nickname": user.nickname,
            "sex": user.sex,
            "birth_year": user.birth_year,
            "books_per_month": user.books_per_month,
        })
        
# -----------------------------
# 토큰 반환 API
# -----------------------------
class CurrentUserTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        token, _ = Token.objects.get_or_create(user=request.user)
        return Response({"token": token.key})