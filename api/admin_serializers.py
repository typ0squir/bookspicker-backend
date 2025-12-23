from rest_framework import serializers
from .models import AuthorRole

class AdminContributorSerializer(serializers.Serializer):
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=AuthorRole.choices)
    is_primary = serializers.BooleanField()


class AdminBookCreateSerializer(serializers.Serializer):
    isbn = serializers.CharField()
    title = serializers.CharField()
    subtitle = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    publisher = serializers.CharField()

    published_date = serializers.DateField()
    page_count = serializers.IntegerField()
    series_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    lang = serializers.CharField()

    purchase_link = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    genre_child_id = serializers.IntegerField()
    
    # AI / Description Fields
    abstract_descript = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    full_descript = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    top_tags = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    recommendation_refer = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True) # "Why Picked"

    cover_image = serializers.URLField()
    epub_file = serializers.URLField()

    toc = serializers.ListField(child=serializers.DictField())
    contributors = AdminContributorSerializer(many=True)

    def validate_contributors(self, value):
        primary_count = sum(1 for c in value if c["is_primary"])
        if primary_count != 1:
            raise serializers.ValidationError("대표 작가는 정확히 1명이어야 합니다.")
        return value

class AdminAuthorListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    profile_image = serializers.URLField(allow_null=True)
    bio = serializers.CharField(allow_blank=True)
