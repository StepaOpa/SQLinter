#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример использования SQLSearcher для поиска SQL запросов.
"""

import os
import sys

# Добавляем путь к модулю sql_searcher
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sql_searcher import SQLSearcher


def main():
    """Основная функция демонстрации работы SQLSearcher."""
    
    # Заголовок
    print("=" * 60)
    print("SQL SEARCHER - Поиск SQL запросов в Python файлах")
    print("=" * 60)
    
    # Создаем экземпляр поисковика
    searcher = SQLSearcher()
    
    # Примеры строк для тестирования
    test_strings = [
        'SELECT * FROM users WHERE id = 1',
        'INSERT INTO table VALUES (1, 2, 3)',  
        'print("Hello World")',
        'SELCT * FROM users',  # С опечаткой
        'UPDATE users SET status = "active"',
        'from datetime import datetime',  # Python import
        'def get_users():',  # Python function
        'Please SELECT your option',  # Естественный язык
    ]
    
    print("\n1. ТЕСТИРОВАНИЕ is_sql_query:")
    print("-" * 40)
    
    for i, test_string in enumerate(test_strings, 1):
        is_sql = searcher.is_sql_query(test_string)
        emoji = "[SQL]" if is_sql else "[PYTHON]"
        print(f"{i:2d}. {emoji} {test_string}")
    
    print("\n2. АНАЛИЗ РЕАЛЬНЫХ ФАЙЛОВ:")
    print("-" * 40)
    
    # Получаем путь к тестовым файлам
    test_dir = os.path.dirname(__file__)
    
    # Ищем Python файлы в директории
    python_files = []
    for file in os.listdir(test_dir):
        if file.endswith('.py') and file != os.path.basename(__file__):
            python_files.append(os.path.join(test_dir, file))
    
    # Если нет файлов, создаем тестовый файл
    if not python_files:
        test_file = os.path.join(test_dir, 'temp_test_sql.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
# Тестовый файл с SQL запросами

def get_users():
    query = "SELECT * FROM users WHERE active = 1"
    return query

def bad_query():
    bad_query = "SELCT * FROM users"  # Опечатка в SELECT
    another_bad = "INSERT INTO users VALUES (1, 'test')"  # Опечатка в INSERT
    return bad_query, another_bad

# F-strings с SQL
def dynamic_query(table_name):
    query = f"SELECT * FROM {table_name} WHERE active = 1"
    return query

# Строка с SQL внутри документации
def update_user_status():
    """
    Функция для обновления статуса пользователя.
    
    SQL: UPDATE users SET status = 'active' WHERE id = ?
    """
    connection = sqlite3.connect('db.sqlite')
    cursor = connection.cursor()
    
    # Еще один запрос
    delete_sql = "DELETE FROM sessions WHERE expired_at < NOW()"
    cursor.execute(delete_sql)
    
    connection.commit()
    connection.close()

# DDL запросы
def create_tables():
    create_users_table = """
    CREATE TABLE users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE
    )
    """
    return create_users_table
''')
        python_files = [test_file]
    
    # Анализируем каждый файл
    total_queries = 0
    for file_path in python_files:
        print(f"\nФайл: {os.path.basename(file_path)}")
        print("-" * 20)
        
        try:
            results = searcher.find_sql_in_file(file_path)
            print(f"   Найдено SQL запросов: {len(results)}")
            total_queries += len(results)
            
            for i, result in enumerate(results, 1):
                print(f"   {i:2d}. Строка {result.get('line', '?')}, позиция {result['start_pos']}-{result['end_pos']}")
                
                # Выводим расширенную информацию о позициях (если есть) 
                if 'start_line' in result and 'start_column' in result:
                    print(f"       Точная позиция: строка {result['start_line']}, колонка {result['start_column']}-{result['end_column']}")
                
                print(f"       Содержимое: {repr(result['sql_query'][:80])}...")
                
                # Показываем содержимое строки для отладки (если есть)
                if 'line_content' in result:
                    print(f"       Строка кода: {repr(result['line_content'][:100])}")
                
                print()
                
        except Exception as e:
            print(f"   Ошибка при анализе: {e}")
    
    print(f"\nИтого найдено SQL запросов: {total_queries}")
    
    # Удаляем временный файл, если создавали
    temp_file = os.path.join(test_dir, 'temp_test_sql.py')
    if os.path.exists(temp_file):
        try:
            os.remove(temp_file)
            print(f"Временный файл {temp_file} удален.")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 60)


if __name__ == "__main__":
    main() 