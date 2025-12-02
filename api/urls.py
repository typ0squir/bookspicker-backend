from django.urls import path
from .views import (
    BookListView, BookDetailView,
    LibraryListView, LibraryDetailView, BookDownloadView,
    WishlistListView, WishlistDetailView,
    HighlightListView, HighlightDetailView,
    HistoryListView, HistoryDetailView,
    RecommendationView, MeView, CurrentUserTokenView
)

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:isbn>/', BookDetailView.as_view(), name='book-detail'),
    
    path('library/', LibraryListView.as_view(), name='library-list'),
    path('library/<int:isbn>/', LibraryDetailView.as_view(), name='library-detail'),
    path('library/<int:isbn>/download/', BookDownloadView.as_view(), name='book-download'),
    
    path('wishlist/', WishlistListView.as_view(), name='wishlist-list'),
    path('wishlist/<int:isbn>/', WishlistDetailView.as_view(), name='wishlist-detail'),
    
    path('highlights/', HighlightListView.as_view(), name='highlight-list'),
    path('highlights/<int:pk>/', HighlightDetailView.as_view(), name='highlight-detail'),
    
    path('history/', HistoryListView.as_view(), name='history-list'),
    path('history/<int:isbn>/', HistoryDetailView.as_view(), name='history-detail'),
    
    path('recommendations/', RecommendationView.as_view(), name='recommendation-list'),
    
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/token/', CurrentUserTokenView.as_view(), name='current-user-token'),
]
