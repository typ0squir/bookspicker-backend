import os
import django
import random

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookspicker.settings")
django.setup()

from api.models import Book

def randomize_stats():
    print("Randomizing book statistics...")
    books = Book.objects.all()
    count = 0
    for book in books:
        # Generate random values for statistics
        # readed_num_week: 0 to 50
        book.readed_num_week = random.randint(0, 50)
        
        # readed_num_month: week stats + random (e.g. 0 to 200) to ensure month >= week
        book.readed_num_month = book.readed_num_week + random.randint(0, 200)
        
        # like_count: 0 to 100
        book.like_count = random.randint(0, 100)
        
        book.save()
        count += 1
        
    print(f"Successfully updated statistics for {count} books.")

if __name__ == "__main__":
    randomize_stats()
