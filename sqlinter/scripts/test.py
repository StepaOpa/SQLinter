import psycopg2
from typing import List, Dict, Any


def execute_query(query: str) -> List[Dict[str, Any]]:
    conn = psycopg2.connect("dbname=test user=postgres")
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


class UserService:
    @staticmethod
    def get_active_users() -> List[Dict[str, Any]]:
        query = "SELECT id, name, email FROM users WHERE status = 'active'"
        return execute_query(query)

    @staticmethod
    def search_users(name_filter: str) -> List[Dict[str, Any]]:
        query = f'SELECT * FROM users WHERE name LIKE \'%{name_filter}%\''
        return execute_query(query)


class OrderService:
    @staticmethod
    def get_recent_orders(days: int = 30) -> List[Dict[str, Any]]:
        query = '''
            SELECT o.id, o.date, u.name
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.date > NOW() - INTERVAL '%s days'
        ''' % days
        return execute_query(query)

    @staticmethod
    def create_order(user_id: int, items: List[int]) -> None:
        query = "INSERT INTO orders (user_id, items) VALUES (%s, '%s')" % (
            user_id,
            "{" + ",".join(map(str, items)) + "}"
        )
        execute_query(query)

# utils.py - вспомогательные функции


def generate_complex_report() -> List[Dict[str, Any]]:
    query = """
        WITH user_stats AS (
            SELECT
                u.id,
                u.name,
                COUNT(o.id) as order_count,
                SUM(o.amount) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            GROUP BY u.id, u.name
        )
        SELECT * FROM user_stats
        WHERE order_count > 0
        ORDER BY total_spent DESC
    """
    return execute_query(query)


def cleanup_old_data(table: str, days: int) -> None:
    query = f'''DELETE FROM "{table}" WHERE created_at < NOW() - INTERVAL '{days} days''''
    execute_query(query)