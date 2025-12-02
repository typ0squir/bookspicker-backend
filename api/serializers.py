from rest_framework import serializers
from .models import Book, Trait, Tag, BookTag, Highlight, Library, Wishlist, UserBookHistory, Author, AuthorsBook

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'author_name', 'introduction']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'content']

class AuthorsBookSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='author.author_name')
    role = serializers.CharField()

    class Meta:
        model = AuthorsBook
        fields = ['name', 'role']

class BookSerializer(serializers.ModelSerializer):
    authors = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'

    def get_authors(self, obj):
        authors_books = AuthorsBook.objects.filter(book=obj)
        return AuthorsBookSerializer(authors_books, many=True).data

    def get_tags(self, obj):
        book_tags = BookTag.objects.filter(book=obj)
        return [bt.tag.content for bt in book_tags]

class LibrarySerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()

    class Meta:
        model = Library
        fields = '__all__'
        read_only_fields = ('user', 'added_at')

    def get_book(self, obj):
        try:
            book = Book.objects.get(isbn=obj.isbn)
            return BookSerializer(book).data
        except Book.DoesNotExist:
            return None

class WishlistSerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = '__all__'
        read_only_fields = ('user', 'added_at')

    def get_book(self, obj):
        try:
            book = Book.objects.get(isbn=obj.isbn)
            return BookSerializer(book).data
        except Book.DoesNotExist:
            return None

class HighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlight
        fields = '__all__'
        read_only_fields = ('user', 'created_at')

class UserBookHistorySerializer(serializers.ModelSerializer):
    book = serializers.SerializerMethodField()

    class Meta:
        model = UserBookHistory
        fields = '__all__'
        read_only_fields = ('user', 'started_at')

    def get_book(self, obj):
        try:
            book = Book.objects.get(isbn=obj.isbn)
            return BookSerializer(book).data
        except Book.DoesNotExist:
            return None
