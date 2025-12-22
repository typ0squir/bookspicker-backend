from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    path('coldstart/nickname/', views.coldstart_nickname),
    path("coldstart/tags/", views.coldstart_tags),
    path("coldstart/books/", views.coldstart_books),
    path("coldstart/profile_info/", views.coldstart_profile_info),

    path("nickname/", views.nickname_update),
    path("resign/", views.resign),
    path("social-login/", views.social_login),

    path("highlights/", views.highlights_list),
    path("comments/", views.comment_list),
    path("booklist/", views.booklist),
]