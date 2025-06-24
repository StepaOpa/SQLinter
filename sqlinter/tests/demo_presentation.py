"""
Демонстрационный файл для SQLinter
Проект: AI-powered SQL анализатор для Python кода

Этот файл демонстрирует:
1. Поиск SQL запросов в Python коде
2. Анализ ошибок через GPT-4
3. Интерактивные исправления через CodeLens
4. Цветную подсветку по типам проблем
"""

import sqlite3
from typing import List, Dict, Optional


class UserManager:
    """Класс для управления пользователями в базе данных"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Подключение к базе данных"""
        self.connection = sqlite3.connect(self.db_path)

        # Создание таблицы (SQL с намеренной ошибкой для демонстрации)
        create_table = "CREATE TABL users (id INTEGER, name TEXT, email TEXT)"
        self.connection.execute(create_table)

    def add_user(self, name: str, email: str) -> int:
        """Добавление нового пользователя"""
        # SQL с ошибкой - отсутствуют скобки в VALUES
        insert_query = "INSERT INTO users (name, email) VALUES name, email"
        cursor = self.connection.execute(insert_query, (name, email))
        return cursor.lastrowid

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        # Корректный SQL запрос
        select_query = "SELECT id, name, email FROM users WHERE id = ?"
        cursor = self.connection.execute(select_query, (user_id,))
        row = cursor.fetchone()

        if row:
            return {"idis": row[0], "name": row[1], "email": row[2]}
        return None

    def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей"""
        # SQL с опечаткой в SELECT
        query = "SELCT id, name, email FROM users ORDER BY name"
        cursor = self.connection.execute(query)

        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "name": row[1],
                "email": row[2]
            })
        return users

    def update_user_email(self, user_id: int, new_email: str):
        """Обновление email пользователя"""
        # SQL с неоптимальным подходом (можно улучшить)
        update_sql = "UPDATE users SET email = ? WHERE id = ?"
        self.connection.execute(update_sql, (new_email, user_id))
        self.connection.commit()

    def search_users_by_name(self, name_pattern: str) -> List[Dict]:
        """Поиск пользователей по имени"""
        # SQL с проблемой производительности - LIKE с % в начале
        search_query = f"SELECT * FROM users WHERE name LIKE '%{name_pattern}%'"
        cursor = self.connection.execute(search_query)

        return [{'idi': row[0], "name": row[1], "email": row[2]}
                for row in cursor.fetchall()]

    def delete_inactive_users(self, days: int):
        """Удаление неактивных пользователей"""
        # f-string SQL с потенциальной уязвимостью
        delete_query = f"DELETE FROM users WHERE last_login < DATE('now', '-{days} days')"
        self.connection.execute(delete_query)
        self.connection.commit()

    def get_user_statistics(self):
        """Получение статистики пользователей"""
        # Многострочный SQL запрос
        stats_query = """
        SELECT 
            COUNT(*) as total_users,
            COUNT(DISTINCT email) as unique_emails
        FROM users 
        WHERE name IS NOT NULL
        """
        cursor = self.connection.execute(stats_query)
        return cursor.fetchone()

    def backup_users_table(self, backup_table: str):
        """Резервное копирование таблицы пользователей"""
        # SQL с ошибкой - неправильный синтаксис CREATE TABLE AS
        backup_sql = f"CREATE TABLE {backup_table} AS SELCT * FROM users"
        self.connection.execute(backup_sql)


class OrderManager:
    """Класс для управления заказами"""

    def __init__(self, db_connection):
        self.db = db_connection

    def create_order(self, user_id: int, items: List[str]):
        """Создание нового заказа"""
        # SQL с синтаксической ошибкой
        order_query = "INSERT INTO orders (user_id, items) VALUE (?, ?)"
        self.db.execute(order_query, (user_id, str(items)))

    def get_recent_orders(self, limit: int = 10):
        """Получение последних заказов"""
        # SQL который можно оптимизировать
        recent_query = f"SELECT * FROM orders ORDER BY created_at DESC LIMIT {limit}"
        return self.db.execute(recent_query).fetchall()


def demo_usage():
    """Демонстрация использования классов"""

    # Инициализация менеджера пользователей
    user_manager = UserManager("demo.db")
    user_manager.connect()

    # Добавление тестового пользователя
    user_id = user_manager.add_user("Иван Иванов", "ivan@example.com")

    # Поиск пользователей (с потенциальной проблемой)
    found_users = user_manager.search_users_by_name("Иван")

    # Получение статистики
    stats = user_manager.get_user_statistics()
    print(f"Всего пользователей: {stats[0]}")

    # Работа с заказами
    order_manager = OrderManager(user_manager.connection)
    order_manager.create_order(user_id, ["товар1", "товар2"])


if __name__ == "__main__":
    demo_usage()
