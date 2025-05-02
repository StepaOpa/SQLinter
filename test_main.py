import pytest
from sql_extractor_v2 import main

TEST_CASES = [
    {
        "name": "Разные кавычки в одном файле",
        "input": """
            cursor.execute("SELECT * FROM table1")
            cursor.execute('SELECT * FROM table2')
            cursor.execute('''SELECT * FROM table3''')
        """.strip(),  
        "expected": [
            '"SELECT * FROM table1"',
            "'SELECT * FROM table2'",
            "'''SELECT * FROM table3'''"
        ]
    },
    {
        "name": "Прямые запросы с разными кавычками",
        "input": """
            cursor.execute('SELECT * FROM users')
            cursor.execute("SELECT * FROM products")
            cursor.execute('''SELECT id, name FROM customers''')
            cursor.execute(\"\"\"SELECT * FROM orders WHERE status = 'active'\"\"\")
        """.strip(),
        "expected": [
            "'SELECT * FROM users'",
            '"SELECT * FROM products"',
            "'''SELECT id, name FROM customers'''",
            '\"\"\"SELECT * FROM orders WHERE status = \'active\'\"\"\"'
        ]
    },
    {
        "name": "Запросы через переменные с разными кавычками",
        "input": """
            query1 = 'DELETE FROM temp_table'
            cursor.execute(query1)
            query2 = "UPDATE users SET last_login = NOW()"
        """.strip(),
        "expected": [
            "'DELETE FROM temp_table'"
        ]
    },
    {
        "name": "иные ситуации",
        "input": """
            cur.execute('SELECT * FROM "users"') 
        """.strip(),
        "expected": [
            '\'SELECT * FROM "users"\''
        ]
    },
    {
        "name": "ыыы",
        "input": """
            query3 = "djfshskdfhkjsdf"
            cursory.fetch(query3)
        """.strip(),
        "expected": [
            "\"djfshskdfhkjsdf\""
        ]
    },
    {
        "name": "10",
        "input": '''
            curs.execute("""
                INSERT INTO config (data) 
                VALUES ('{"theme": "dark", "lang": "en"}')
            """)
        '''.strip(),
        "expected": [
            '''"""
                INSERT INTO config (data) 
                VALUES ('{"theme": "dark", "lang": "en"}')
            """'''
        ]
    },
    {
        "name": "11",
        "input": """
                cursor.execute('''
                    SELECT 
                        u.name, 
                        array_agg(p.title) AS posts 
                    FROM users u
                    LEFT JOIN posts p ON p.user_id = u.id
                    WHERE u.rating > %s
                    GROUP BY u.name
                ''')
        """.strip(),
        "expected": [
                    """'''
                    SELECT 
                        u.name, 
                        array_agg(p.title) AS posts 
                    FROM users u
                    LEFT JOIN posts p ON p.user_id = u.id
                    WHERE u.rating > %s
                    GROUP BY u.name
                '''"""
        ]
    },
    {
        "name": "12",
        "input": '''
            sql_query = ("""
                WITH cte AS (
                    SELECT user_id, SUM(amount) total 
                    FROM transactions 
                    WHERE currency='USD'
                )
                SELECT * FROM cte WHERE total > %s
            """)
            c.fetch(sql_query, (1000,))
        '''.strip(),
        "expected": [
            '''"""
                WITH cte AS (
                    SELECT user_id, SUM(amount) total 
                    FROM transactions 
                    WHERE currency='USD'
                )
                SELECT * FROM cte WHERE total > %s
            """'''
        ]
    },
    {
        "name": "13",
        "input": '''
            sql12 = """
                INSERT INTO sensors (temp, timestamp) 
                VALUES (?, ?)
            """
            cursor.executemany(sql12, [(25.3, '2023-10-01'), (26.1, '2023-10-02')])
        '''.strip(),
        "expected": [
            '''"""
                INSERT INTO sensors (temp, timestamp) 
                VALUES (?, ?)
            """'''
        ]
    },
    {
        "name": "14",
        "input": '''
            sql13 = """
                COPY employees(name, position) 
                FROM STDIN WITH (FORMAT CSV)
            """
            cursor.copy_expert(sql13, data_file)
        '''.strip(),
        "expected": [
            '''"""
                COPY employees(name, position) 
                FROM STDIN WITH (FORMAT CSV)
            """'''
        ]
    }
]

@pytest.mark.parametrize("test_case", TEST_CASES)
def test_multiple_queries(tmp_path, test_case):
    # Создаем временный файл
    test_file = tmp_path / "test_script.py"
    test_file.write_text(test_case["input"])#записываем все во временный файл
    
    # Запускаем парсер с этим файлом
    extracted_sql = main(test_file)
    
    # Проверяем, что количество запросов совпадает
    assert len(extracted_sql) == len(test_case["expected"]), \
        f"Ожидалось наличие {len(test_case['expected'])} запросов, а найдено было {len(extracted_sql)}"

    #проверяем, что все запросы найдены
    for expected_sql in test_case["expected"]:
        assert expected_sql in extracted_sql
    
    