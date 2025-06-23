#!/usr/bin/env python3

# Импортируем наш SQL searcher
from sql_searcher import SQLSearcher
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))


# Создаем простой тестовый Python код с SQL
test_code = '''
def get_users():
    query = "SELECT * FROM users WHERE age > 18"
    return query

def bad_query():
    sql = "SELCT * FORM users"  # С опечатками
    return sql
'''

# Сохраняем в файл
with open('temp_test.py', 'w', encoding='utf-8') as f:
    f.write(test_code)

# Тестируем наш searcher
searcher = SQLSearcher()
results = searcher.find_sql_in_file('temp_test.py')

print(f"Найдено SQL запросов: {len(results)}")
for i, result in enumerate(results, 1):
    print(f"{i}. Запрос: {repr(result['sql_query'])}")
    print(f"   Позиция: {result['start_pos']}-{result['end_pos']}")
    print(f"   Строка: {result.get('line', 'N/A')}")
    print()

# Удаляем тестовый файл
os.remove('temp_test.py')
print("Тест завершен!")
