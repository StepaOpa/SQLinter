#!/usr/bin/env python3
"""
Тестовый файл с примерами SQL запросов для демонстрации работы sql_searcher.py
"""

import sqlite3
import psycopg2

# Обычные SQL запросы


def get_users():
    query = "SELECT * FROM users WHERE age > 18"
    return query


def insert_user(name, email):
    sql = "INSERT INTO users (name, email) VALUES (?, ?)"
    return sql

# Многострочные SQL запросы


def complex_query():
    query = """
    SELECT u.name, u.email, p.title 
    FROM users u 
    JOIN posts p ON u.id = p.user_id 
    WHERE u.created_at > '2023-01-01'
    ORDER BY u.name
    """
    return query

# SQL с опечатками


def typo_query():
    bad_query = "SELCT * FORM users"  # Опечатки в SELECT и FROM
    another_bad = "INSERTT INTO users VALUES (1, 'test')"  # Опечатка в INSERT
    return bad_query, another_bad

# F-strings с SQL


def dynamic_query(table_name):
    query = f"SELECT * FROM {table_name} WHERE active = 1"
    return query

# Строка с SQL внутри функции


def update_user_status():
    connection = sqlite3.connect('database.db')
    cursor = connection.cursor()

    update_sql = "UPDATE users SET status = 'active' WHERE id = ?"
    cursor.execute(update_sql, (1,))

    # Еще один запрос
    delete_sql = "DELETE FROM sessions WHERE expired_at < NOW()"
    cursor.execute(delete_sql)

    connection.commit()
    connection.close()

# DDL запросы


def create_tables():
    create_users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """

    create_posts_table = """
    CREATE TABLE posts (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255),
        content TEXT,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """

    return create_users_table, create_posts_table

# SQL с опечатками в более сложных запросах


def advanced_typos():
    # Опечатка в GROUP BY
    query1 = "SELECT COUNT(*) FORM users GRUP BY status"

    # Опечатка в WHERE
    query2 = "SELECT * FROM posts WERE user_id = 1"

    # Опечатка в ORDER BY
    query3 = "SELECT * FROM users ODER BY name"

    return query1, query2, query3

# Не SQL строки (не должны быть найдены)


def not_sql():
    message = "Hello, this is not SQL"
    filename = "data.txt"
    html = "<div>This is HTML</div>"
    return message, filename, html

# Смешанные строки


def mixed_content():
    # Эта строка содержит SQL
    mixed = "Error in SQL: SELECT * FROM users WHERE id = 1"

    # А эта - нет
    normal = "The user selected option FROM the menu"

    return mixed, normal

# PostgreSQL специфичные запросы


def postgres_queries():
    # UPSERT
    upsert_query = """
    INSERT INTO users (id, name, email) 
    VALUES (1, 'John', 'john@example.com')
    ON CONFLICT (id) 
    DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email
    """

    # Оконные функции
    window_query = """
    SELECT name, salary,
           ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
    FROM employees
    """

    return upsert_query, window_query

# JSON запросы


def json_queries():
    json_query = """
    SELECT data->'name' as name, data->'age' as age
    FROM users_json
    WHERE data->>'status' = 'active'
    """
    return json_query


if __name__ == "__main__":
    print("Тестовый файл с SQL запросами")
    print("Используйте sql_searcher.py для поиска SQL в этом файле")
