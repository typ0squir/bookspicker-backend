from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    path('books/', views.book_list, name='book-list'),
    path('books/<int:isbn>/', views.book_detail, name='book-detail'),
    path('books/popular/', views.popular_books, name='book-popular'),
    path('books/search/', views.search_books, name='book-search'),
    path('books/<int:isbn>/review/', views.create_review, name='review-create'),
    path('books/<str:isbn>/review/<int:review_id>/', views.review_detail, name='review-detail'),
    path("books/<str:isbn>/likes", views.book_like_toggle, name="book-like-toggle"),
]