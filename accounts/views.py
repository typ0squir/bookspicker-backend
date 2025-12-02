from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .serializers import UserSerializer

User = get_user_model()

class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="회원가입",
        description="새로운 사용자를 생성하고 토큰을 반환합니다.",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully. Returns user info and token."
            ),
            400: OpenApiResponse(description="Bad Request")
        }
    )
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(ObtainAuthToken):
    @extend_schema(
        summary="로그인",
        description="사용자명과 비밀번호로 로그인하고 토큰을 반환합니다.",
        responses={
            200: OpenApiResponse(
                description="Login successful",
                response={
                    "type": "object",
                    "properties": {
                        "token": {"type": "string"},
                        "user_id": {"type": "integer"},
                        "username": {"type": "string"}
                    }
                }
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username
        })

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="로그아웃",
        description="현재 사용자의 토큰을 삭제하여 로그아웃 처리합니다.",
        responses={200: OpenApiResponse(description="Successfully logged out.")}
    )
    def post(self, request):
        request.user.auth_token.delete()
        return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary="내 프로필 조회", description="현재 로그인한 사용자의 프로필 정보를 조회합니다.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary="내 프로필 수정", description="현재 로그인한 사용자의 프로필 정보를 수정합니다.")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(summary="내 프로필 수정 (PUT)", description="현재 로그인한 사용자의 프로필 정보를 전체 수정합니다.", exclude=True)
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def get_object(self):
        return self.request.user
