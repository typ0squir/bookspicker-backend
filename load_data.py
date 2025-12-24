import os
import django
import json

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookspicker.settings")
django.setup()

from api.models import Author, GenreParent, GenreChild

def load_authors():
    print("Loading authors...")
    file_path = os.path.join("api", "fixtures", "author.json")
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        created_count = 0
        for item in data:
            _, created = Author.objects.get_or_create(
                name=item["name"],
                defaults={
                    "profile_image": item["profile_image"],
                    "bio": item["bio"]
                }
            )
            if created:
                created_count += 1
    print(f"Authors loaded. ({created_count} new)")

def load_genres():
    print("Loading genres...")
    
    # Load Parents
    parents_path = os.path.join("api", "fixtures", "genre_parents.json")
    if not os.path.exists(parents_path):
        print(f"File not found: {parents_path}")
        return

    with open(parents_path, "r", encoding="utf-8") as f:
        parents_data = json.load(f)
        for item in parents_data:
            GenreParent.objects.get_or_create(name=item["name"])
    
    # Load Children
    children_path = os.path.join("api", "fixtures", "genre_children.json")
    if not os.path.exists(children_path):
        print(f"File not found: {children_path}")
        return

    with open(children_path, "r", encoding="utf-8") as f:
        children_data = json.load(f)
        for item in children_data:
            parent_name = item["parent_key"]
            child_name = item["name"]
            
            try:
                parent = GenreParent.objects.get(name=parent_name)
                GenreChild.objects.get_or_create(
                    parent=parent,
                    name=child_name
                )
            except GenreParent.DoesNotExist:
                print(f"Parent genre '{parent_name}' not found for child '{child_name}'")

    print("Genres loaded.")

if __name__ == "__main__":
    load_authors()
    load_genres()
