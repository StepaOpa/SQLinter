import os
from openai import OpenAI
import ast
import json
from typing import List, Union


class GPTModel(OpenAI):
    def __init__(self, api_key, sqlquerries):
        self.api_key = api_key
        self.sqlquerries = sqlquerries
        self._parsed_queries = None
        if not self.api_key:
            raise ValueError(
                "Please set the OPENAI_API_KEY environment variable")
        super().__init__(api_key=self.api_key)

    def _get_raw_gpt_output(self, sqlquerries) -> str:
        prompt = (f'''
                Это входящие SQL запросы взятые из реального проекта:{sqlquerries}. Твоя задача определить их правильность 
                и вынести вердикты в виде True или False. True - запрос правильный, Error - запрос абсолютно неправильный, Warning - запрос правильный, но можно сделать лучше.
                Если вердикт Error или Warning, то ты должен вынести причину, почему он неправильный и переделать этот запрос чтоб он стал правильным.
                Если запрос правильный, то ничего не выводи.
                На выходе мне надо получить python список вида [['входящий sql запрос', 'вердикт', 'причина, почему он неправильный'], ['входящий sql запрос', 'вердикт', 'причина, почему он неправильный']]
                Я буду этот список передавать далее для обработки в другом скрипте, поэтому в твоем ответе не должно быть ничего кроме этого списка. 
                Комментарии пиши на русском языке
                '''
                  )

        response = self.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system",
                    "content": "You are a helpful assistant that corrects SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=512
        )
        output = response.choices[0].message.content.strip()
        # print(response.choices[0].message.content.strip())
        return output

    def _clean_gpt_output(self, gpt_output: str) -> str:
        lines = gpt_output.splitlines()
        if len(lines) > 2:
            return '\n'.join(lines[1:-1])
        return gpt_output

    def _parse_queries(self) -> Union[List, None]:
        """Парсинг очищенного вывода в список Python"""
        try:
            raw_gpt_output = self._get_raw_gpt_output(self.sqlquerries)
            cleaned_output = self._clean_gpt_output(raw_gpt_output)
            self.parsed_queries = ast.literal_eval(cleaned_output)
            return self.parsed_queries
        except (SyntaxError, ValueError, IndexError) as e:
            print(f"Ошибка парсинга: {e}")
            return None

    @property
    def queries(self) -> str:
        """
        Геттер для получения отформатированного JSON из проанализированных SQL-запросов.

        Returns:
            str: Отформатированный JSON для проанализированных SQL-запросов.
        """
        if not self._parsed_queries:
            self._parse_queries()

        if self.parsed_queries:
            return json.dumps(self.parsed_queries, indent=2, ensure_ascii=False)
        return json.dumps([], indent=2)

# test
# if __name__ == "__main__":
#     # sqlquerries = ['"SELECT id, name, email FROM users WHERE status=\'active\'"', "'''\n             SELECT o.id, o.date, u.name \n             FROM orders o\n             JOIN users u ON o.user_id = u.id\n             WHERE o.date > NOW() - INTERVAL '%s days'\n        '''",
#     #                '"""\n        WITH user_stats AS (\n            SELECT \n                u.id,\n                u.name,\n                COUNT(o.id) as order_count,\n                SUM(o.amount) as total_spent\n            FROM users u\n            LEFT JOIN orders o ON u.id = o.user_id\n            GROUP BY u.id, u.name\n        )\n        SELECT * FROM user_stats \n        WHERE order_count > 0\n        ORDER BY total_spent DESC\n    """', "f'SELECT * FROM users WHERE name LIKE \\'", 'f\'\'\'DELETE FROM "{table}" WHERE created_at < NOW() - INTERVAL \'{days} days\'\'\'', '"INSERT INTO orders (user_id, items) VALUES (%s, \'%s\')"']
#     sqlquerries = ["CREATE TABLE IF NOT EXISTS Users",
#                    "SELECT id, name, email FROM users WHERE status = 'active'"]
#     api_key = os.getenv("OPENAI_API_KEY")
#     gpt = GPTModel(api_key, sqlquerries=sqlquerries)
#     print(gpt.queries)
