from rest_framework.permissions import BasePermission

class IsActiveUser(BasePermission):
    """
    인증되어 있고, 탈퇴/비활성 계정이 아닌 사용자만 허용
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return getattr(user, "is_active", True) is True