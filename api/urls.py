from django.urls import path
from . import views

app_name = 'api'
urlpatterns = [
    # books
    path("books/<str:isbn>/", views.book_detail),
    path("books/<str:isbn>/likes/", views.book_like_toggle),
    path("books/<str:isbn>/wishlist/", views.book_wishlist_toggle),
    path("books/<str:isbn>/comment/", views.book_comment),
    path("books/<str:isbn>/library/", views.add_book_to_library),

    # bookviews
    path("bookviews/<str:isbn>/", views.bookview_meta),
    path("bookviews/<str:isbn>/content/", views.bookview_content),

    # main
    path("main/current-reading/", views.main_current_reading),
]