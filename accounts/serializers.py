from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'nickname', 'sex', 'birth_year', 'books_per_month')
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            nickname=validated_data.get('nickname', ''),
            sex=validated_data.get('sex', ''),
            birth_year=validated_data.get('birth_year'),
            books_per_month=validated_data.get('books_per_month', 0)
        )
        return user
