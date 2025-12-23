import os
import sqlite3
from django.conf import settings
import django

# Django 환경 설정 (DB 경로를 가져오기 위해)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bookspicker.settings')
django.setup()

def drop_all_tables():
    # settings.DATABASES에서 데이터베이스 정보 가져오기
    db_settings = settings.DATABASES['default']
    
    if db_settings['ENGINE'] != 'django.db.backends.sqlite3':
        print("이 스크립트는 SQLite3 데이터베이스 전용입니다.")
        return

    db_path = db_settings['NAME']
    
    if not os.path.exists(db_path):
        print(f"데이터베이스 파일이 존재하지 않습니다: {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 모든 테이블 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("삭제할 테이블이 없습니다.")
            return

        print(f"총 {len(tables)}개의 테이블을 발견했습니다.")
        
        # 외래 키 제약 조건 비활성화 (테이블 삭제 순서 문제 방지)
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        for table_name in tables:
            table = table_name[0]
            # sqlite_sequence는 자동 증가값을 관리하는 내부 테이블이므로 삭제하지 않거나 무시 가능하지만, 
            # 깔끔하게 초기화하려면 삭제해도 됨. 단, sqlite_master 테이블은 삭제 불가.
            if table.startswith('sqlite_'):
                continue
                
            print(f"테이블 삭제 중: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS \"{table}\";")
        
        # 외래 키 제약 조건 다시 활성화
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        conn.commit()
        conn.close()
        print("\n모든 테이블이 성공적으로 삭제되었습니다.")
        print("이제 'python manage.py migrate'를 실행하여 테이블을 다시 생성하세요.")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    confirm = input("경고: 모든 데이터베이스 테이블과 데이터가 영구적으로 삭제됩니다.\n계속하시겠습니까? (y/n): ")
    if confirm.lower() == 'y':
        drop_all_tables()
    else:
        print("작업이 취소되었습니다.")
