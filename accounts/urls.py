from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('coldstart/nickname/', views.coldstart_nickname),
    path("coldstart/tags/", views.coldstart_tags),
    path("coldstart/books/", views.coldstart_books),

]