# SQL Searcher - Поиск SQL запросов в Python файлах

Скрипт для поиска SQL запросов в Python файлах с определением точных позиций. Находит как корректные, так и некорректные SQL запросы (с опечатками).

## 🚀 Возможности

- ✅ Поиск SQL запросов в строках Python кода
- ✅ Обнаружение опечаток в SQL (например: `SELCT` вместо `SELECT`)
- ✅ Определение абсолютных позиций начала и конца запроса
- ✅ Поддержка многострочных SQL запросов (тройные кавычки)
- ✅ Поддержка f-strings с SQL
- ✅ Анализ отдельных файлов и целых директорий
- ✅ Рекурсивный поиск в поддиректориях

## 📋 Формат вывода

Программа возвращает список словарей следующего формата:

```python
[
    {
        'sql_query': 'SELECT * FROM users WHERE age > 18',
        'start_pos': 45,
        'end_pos': 80
    },
    # ... другие найденные запросы
]
```

Где:
- `sql_query` - найденный SQL запрос
- `start_pos` - абсолютная позиция первого символа запроса в файле
- `end_pos` - абсолютная позиция последнего символа запроса в файле

## 🛠 Использование

### Командная строка

```bash
# Анализ одного файла
python sql_searcher.py path/to/your/file.py

# Анализ директории (не рекурсивно)
python sql_searcher.py path/to/directory/

# Рекурсивный анализ директории
python sql_searcher.py path/to/directory/ --recursive
```

### Программное использование

```python
from sql_searcher import SQLSearcher

# Создаем экземпляр поисковика
searcher = SQLSearcher()

# Анализируем файл
results = searcher.find_sql_in_file('my_script.py')

# Проверяем отдельную строку
is_sql = searcher.is_sql_query("SELECT * FROM users")

# Анализируем директорию
all_results = searcher.search_in_directory('./src/', recursive=True)
```

## 🔍 Что ищется

### Корректные SQL запросы:
- `SELECT * FROM users WHERE age > 18`
- `INSERT INTO posts (title, content) VALUES (?, ?)`
- `UPDATE users SET status = 'active'`
- `DELETE FROM sessions WHERE expired = true`
- `CREATE TABLE users (id INT PRIMARY KEY)`

### SQL с опечатками:
- `SELCT * FORM users` (SELECT, FROM)
- `INSERTT INTO table VALUES (1)` (INSERT)
- `UPDAT users SET name = 'test'` (UPDATE)
- `DELET FROM table WHERE id = 1` (DELETE)

### Сложные запросы:
- Многострочные SQL в тройных кавычках
- F-strings с SQL содержимым
- JOIN запросы
- Подзапросы
- Window functions

## 📁 Примеры файлов

См. файлы в папке `tests/`:
- `test_sql_examples.py` - большой набор примеров
- `example_usage.py` - демонстрация использования
- `simple_test.py` - простой тест

## ⚙️ Требования

- Python 3.6+
- Стандартные библиотеки: `ast`, `re`, `os`, `sys`, `typing`

## 🧠 Алгоритм работы

1. **Парсинг AST** - код Python разбирается в Abstract Syntax Tree
2. **Поиск строк** - находятся все строковые литералы
3. **Анализ содержимого** - каждая строка проверяется на SQL содержимое
4. **Определение позиций** - вычисляются абсолютные позиции в файле
5. **Обработка опечаток** - специальные паттерны для распространенных ошибок

## 🎯 Точность поиска

Скрипт использует комбинацию методов для максимальной точности:

- **Сильные индикаторы**: SELECT, INSERT, UPDATE, DELETE, CREATE, DROP
- **Слабые индикаторы**: FROM, WHERE, JOIN, GROUP BY, ORDER BY
- **Комбинированный анализ**: 2+ SQL ключевых слова = SQL запрос
- **Паттерны опечаток**: специальные регулярные выражения

## 🚫 Ограничения

- Может не найти сильно замаскированные SQL запросы
- F-strings обрабатываются упрощенно в старых версиях Python
- Динамически генерируемые запросы могут быть пропущены
- Комментарии внутри SQL не всегда обрабатываются корректно

## 📝 Лицензия

Свободное использование в образовательных целях. 