
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookspicker.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
users = User.objects.all()

print(f"{'ID':<5} {'Username':<15} {'Is Staff':<10} {'Is Superuser':<15}")
print("-" * 50)
for user in users:
    print(f"{user.pk:<5} {user.username:<15} {user.is_staff:<10} {user.is_superuser:<15}")
