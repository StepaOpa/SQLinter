#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from sql_searcher import SQLSearcher

def test_sql_detection():
    """Тестируем обнаружение SQL запросов."""
    searcher = SQLSearcher()
    
    # Тестовые строки
    test_cases = [
        ("SELECT * FROM users", True),
        ("INSERT INTO table VALUES (1, 2)", True),
        ("SELCT * FORM users", True),  # С опечатками
        ("UPDATE users SET name = 'test'", True),
        ("Hello world", False),
        ("SELECT name FROM users WHERE id = 1", True),
        ("This is not SQL", False),
        ("CREATE TABLE users (id INT)", True),
        ("DROP TABLE old_table", True),
        ("INSERTT INTO users VALUES (1)", True),  # Опечатка
    ]
    
    print("=== ТЕСТ ОБНАРУЖЕНИЯ SQL ЗАПРОСОВ ===")
    for test_string, expected in test_cases:
        result = searcher.is_sql_query(test_string)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{test_string[:30]}...' -> {result} (ожидалось: {expected})")
    
    print()

def test_file_analysis():
    """Тестируем анализ файла."""
    print("=== АНАЛИЗ ТЕСТОВОГО ФАЙЛА ===")
    
    # Создаем тестовый файл
    test_content = '''
def get_users():
    query = "SELECT * FROM users WHERE active = 1"
    return query

def insert_data():
    sql = """
    INSERT INTO posts (title, content, user_id)
    VALUES (?, ?, ?)
    """
    return sql

def bad_sql():
    # SQL с опечатками
    typo_query = "SELCT * FORM users WERE id > 10"
    return typo_query

def update_status():
    update_sql = "UPDATE users SET status = 'inactive' WHERE last_login < '2023-01-01'"
    delete_sql = "DELETE FROM sessions WHERE expired = true"
    return update_sql, delete_sql

def not_sql_function():
    message = "This is just a regular string"
    return message
'''
    
    # Сохраняем в файл
    test_file = 'demo_test_file.py'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    # Анализируем файл
    searcher = SQLSearcher()
    results = searcher.find_sql_in_file(test_file)
    
    print(f"Найдено SQL запросов: {len(results)}")
    print()
    
    for i, result in enumerate(results, 1):
        print(f"{i}. SQL ЗАПРОС:")
        print(f"   Строка: {result.get('line', 'N/A')}")
        print(f"   Позиция в файле: {result['start_pos']} - {result['end_pos']}")
        print(f"   Длина: {result['end_pos'] - result['start_pos'] + 1} символов")
        print(f"   Содержимое: {repr(result['sql_query'])}")
        print()
    
    # Показываем содержимое файла с позициями
    print("=== СОДЕРЖИМОЕ ФАЙЛА С ПОЗИЦИЯМИ ===")
    with open(test_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"Общая длина файла: {len(content)} символов")
    print()
    
    # Выделяем найденные SQL запросы в тексте
    highlighted_content = content
    offset = 0
    
    for i, result in enumerate(sorted(results, key=lambda x: x['start_pos']), 1):
        start = result['start_pos'] + offset
        end = result['end_pos'] + 1 + offset
        
        marker = f"<<<SQL{i}>>>"
        end_marker = f"<<<END{i}>>>"
        
        highlighted_content = (
            highlighted_content[:start] + 
            marker + 
            highlighted_content[start:end] + 
            end_marker + 
            highlighted_content[end:]
        )
        
        offset += len(marker) + len(end_marker)
    
    print("Файл с выделенными SQL запросами:")
    print("-" * 50)
    print(highlighted_content)
    print("-" * 50)
    
    # Удаляем тестовый файл
    os.remove(test_file)

if __name__ == "__main__":
    test_sql_detection()
    test_file_analysis()
    print("Демонстрация завершена!") 