import sys
import os
from dotenv import load_dotenv

# Загружаем .env из корня проекта
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Добавляем корень проекта в sys.path чтобы импорты работали
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))