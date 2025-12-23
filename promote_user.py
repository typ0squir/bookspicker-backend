
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookspicker.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
email = "yjsong2153@gmail.com"

try:
    user = User.objects.get(email=email)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print(f"Successfully promoted {user.email} (ID: {user.pk}) to staff/superuser.")
except User.DoesNotExist:
    print(f"User with email {email} does not exist.")
except Exception as e:
    print(f"Error: {e}")
