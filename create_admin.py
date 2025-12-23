import os
import django

# Django 환경 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookspicker.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_admin_user():
    User = get_user_model()
    
    # ID가 1인 사용자가 이미 있는지 확인
    if User.objects.filter(pk=1).exists():
        print("ID가 1인 사용자가 이미 존재합니다.")
        return

    try:
        # ID가 1인 슈퍼유저 생성 (ID 강제 지정 불가한 경우도 있으나, 빈 테이블이면 1번 할당됨)
        # 하지만 명시적으로 id=1을 줄 수 있는지 확인 필요 (일반적으로는 생성 후 확인)
        # 만약 기존 데이터가 있어서 1번이 아니라면 문제되므로 force insert 시도하거나
        # 단순히 생성 후 id 확인
        
        username = "admin"
        email = "admin@example.com"
        password = "admin"
        
        # ID 1을 강제하기 위해 객체 직접 생성 후 저장
        user = User(pk=1, username=username, email=email, nickname="관리자", is_staff=True, is_superuser=True)
        user.set_password(password)
        user.save()
        
        print(f"슈퍼유저 생성 완료: ID={user.pk}, Username={username}, Password={password}")
        
    except Exception as e:
        print(f"사용자 생성 중 오류 발생: {e}")

if __name__ == "__main__":
    create_admin_user()
