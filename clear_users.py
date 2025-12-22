import os
import django

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookspicker.settings')
django.setup()

from accounts.models import User

def clear_users():
    try:
        count = User.objects.count()
        print(f"총 {count}명의 사용자를 삭제합니다...")
        
        # User 삭제 (Trait 등 CASCADE 설정된 모델도 함께 삭제됨)
        User.objects.all().delete()
        
        print("모든 사용자 데이터가 성공적으로 삭제되었습니다.")
    except Exception as e:
        print(f"에러 발생: {e}")

if __name__ == "__main__":
    confirm = input("정말로 모든 사용자 데이터를 삭제하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        clear_users()
    else:
        print("삭제가 취소되었습니다.")
