import re
from typing import List, Dict


def find_sql_queries(file_path: str) -> List[Dict[str, int | str]]:
    """
    Находит SQL-запросы в Python-файле и возвращает их позиции.

    Args:
        file_path: Путь к Python-файлу

    Returns:
        Список словарей с информацией о запросах:
        [{
            'text': str,     # Текст запроса
            'start': int,     # Абсолютная позиция начала
            'end': int,       # Абсолютная позиция конца
            'line': int       # Номер строки (начиная с 1)
        }]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    queries = []
    patterns = [
        # Для cursor.execute('SELECT ...')
        r'(?:execute|executemany)\([\s\S]*?[\'\"](.*?)[\'\"][\s\S]*?\)',

        # Для строковых переменных с SQL
        r'(?:sql|query)\s*=\s*(\'\'\'[\s\S]*?\'\'\'|\"\"\"[\s\S]*?\"\"\"|\'.*?\'|\".*?\")'
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, content):
            text = match.group(1)
            if not is_sql_query(text):
                continue

            start = match.start(1)
            end = match.end(1)
            line = content.count('\n', 0, start) + 1

            queries.append({
                'text': text,
                'start': start,
                'end': end,
                'line': line
            })

    return queries


def is_sql_query(text: str) -> bool:
    """Проверяет, похож ли текст на SQL-запрос"""
    sql_keywords = [
        'SELECT', 'INSERT', 'UPDATE', 'DELETE',
        'CREATE', 'ALTER', 'DROP', 'WITH'
    ]
    text_upper = text.upper()
    return any(keyword in text_upper for keyword in sql_keywords)


# Пример использования
if __name__ == "__main__":
    queries = find_sql_queries('testpy copy.py')
    for query in queries:
        print(f"Line {query['line']}:")
        print(f"Text: {query['text']}")
        print(f"Start: {query['start']}, End: {query['end']}\n")
