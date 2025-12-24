import os
import sys
import django

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookspicker.settings")
django.setup()

from django.contrib.auth import get_user_model

def reset_accounts():
    User = get_user_model()
    print("🗑️  Cleaning 'accounts_user' table in Django Backend...")
    
    try:
        # Delete all users. Django handles cascading deletions if relations are set up correctly.
        # This will delete profiles, recommendations, etc. linked to users.
        count, _ = User.objects.all().delete()
        print(f"✅  Successfully deleted {count} user objects.")
        
    except Exception as e:
        print(f"❌  Failed to delete users: {e}")

if __name__ == "__main__":
    if "-y" in sys.argv:
        confirm = 'y'
    else:
        confirm = input("⚠️  Are you sure you want to clear ALL USERS (Django Backend)? (y/n): ")
    
    if confirm.lower() == 'y':
        reset_accounts()
    else:
        print("❌  Cancelled.")
