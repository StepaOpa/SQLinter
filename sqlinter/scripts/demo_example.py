#!/usr/bin/env python3
"""
Демонстрационный файл с SQL запросами
"""

import sqlite3

def get_users():
    """Получить всех пользователей"""
    query = "SELECT * FROM users WHERE age > 18"
    return query

def insert_user(name, email):
    """Добавить пользователя"""
    sql = "INSERT INTO users (name, email) VALUES (?, ?)"
    return sql

def bad_query():
    """Запрос с опечатками"""
    typo_sql = "SELCT * FORM users WERE id > 10"
    return typo_sql

def complex_query():
    """Сложный запрос"""
    query = """
    SELECT u.name, COUNT(p.id) as posts_count
    FROM users u
    LEFT JOIN posts p ON u.id = p.user_id
    WHERE u.status = 'active'
    GROUP BY u.id
    ORDER BY posts_count DESC
    """
    return query

def not_sql():
    """Обычная функция без SQL"""
    message = "Это не SQL запрос"
    return message 