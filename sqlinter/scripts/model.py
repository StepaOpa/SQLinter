import os
import openai
from openai import OpenAI

def main(sqlquerries):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")

    client = OpenAI(api_key=api_key)

    prompt = (
        "You are a helpful assistant that corrects SQL queries. "
        "Correct and validate SQL queries: Given a list of SQL queries, identify and correct syntax errors, and determine if each query is syntactically correct. "
        "Return a list of tuples in the same order as the input queries, where each tuple contains the original query and either a corrected query if an error was detected, or False if the query is syntactically incorrect or None if the input is not a valid SQL query. "
        "Do not change the old sql queries in the created tuples in any way."
        f"Here is the list:\n{sqlquerries}\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an SQL expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=512
    )

    print(response.choices[0].message.content.strip())

if __name__ == "__main__":
    sqlquerries = ['"SELECT id, name, email FROM users WHERE status=\'active\'"', "'''\n             SELECT o.id, o.date, u.name \n             FROM orders o\n             JOIN users u ON o.user_id = u.id\n             WHERE o.date > NOW() - INTERVAL '%s days'\n        '''", '"""\n        WITH user_stats AS (\n            SELECT \n                u.id,\n                u.name,\n                COUNT(o.id) as order_count,\n                SUM(o.amount) as total_spent\n            FROM users u\n            LEFT JOIN orders o ON u.id = o.user_id\n            GROUP BY u.id, u.name\n        )\n        SELECT * FROM user_stats \n        WHERE order_count > 0\n        ORDER BY total_spent DESC\n    """', "f'SELECT * FROM users WHERE name LIKE \\'", 'f\'\'\'DELETE FROM "{table}" WHERE created_at < NOW() - INTERVAL \'{days} days\'\'\'', '"INSERT INTO orders (user_id, items) VALUES (%s, \'%s\')"']
    main(sqlquerries)
