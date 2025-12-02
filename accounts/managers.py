from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Django 내부 user 생성 기본 메서드
        """
        if not username:
            raise ValueError("Users must have a username")
        if not email:
            raise ValueError("Users must have an email address")

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # createsuperuser 시 필수값 자동 입력
        extra_fields.setdefault('sex', 'unknown')
        extra_fields.setdefault('birth_year', '2000-01-01')
        extra_fields.setdefault('nickname', username)

        return self._create_user(username, email, password, **extra_fields)
