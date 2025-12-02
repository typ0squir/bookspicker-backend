from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import UserManager


# -----------------------------
# 사용자(User)
# -----------------------------
class User(AbstractUser):
    nickname = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField()
    sex = models.CharField(max_length=10, blank=True, null=True)
    birth_year = models.DateField(blank=True, null=True)
    books_per_month = models.IntegerField(default=0)
    
    objects = UserManager() 

    REQUIRED_FIELDS = ['email']

