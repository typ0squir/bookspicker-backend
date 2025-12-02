# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User

    # 관리자 페이지에서 표시할 필드들
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ("Personal info", {'fields': ('email', 'nickname', 'sex', 'birth_year')}),
        ("Permissions", {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ("Important dates", {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

    list_display = ('id', 'username', 'email', 'nickname', 'sex', 'birth_year', 'is_staff')
    search_fields = ('username', 'email', 'nickname')
    ordering = ('id',)
