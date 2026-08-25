import os
from dotenv import load_dotenv

# .env 파일의 내용을 환경변수로 로드
load_dotenv()

# 로드된 환경변수 참조
debug_mode = os.getenv('DEBUG')
secret_key = os.getenv('SECRET_KEY')
server_port = os.getenv('PORT')

print(f"DEBUG: {debug_mode}")
print(f"SECRET_KEY: {secret_key}")
print(f"PORT: {server_port}")

