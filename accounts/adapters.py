from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import PermissionDenied

class AccountAdapter(DefaultAccountAdapter):
    def login(self, request, user):
        # 탈퇴(비활성) 유저 로그인 차단
        if hasattr(user, "is_active") and user.is_active is False:
            raise PermissionDenied("RESIGNED_USER")
        return super().login(request, user)