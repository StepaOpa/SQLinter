from GPT_model import GPTModel
import os
import json
import sys
from SQLinterModel import SQLinterModel
from sql_searcher import SQLSearcher
import locale

# Настройка кодировки для корректного вывода
if sys.platform == "win32":
    # На Windows устанавливаем UTF-8 для вывода
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

query_data_template = {
    "id": 0,
    "query": "",
    "verdict": "",
    "reason": "",
    "correction": "",
    "start": None,
    "end": None
}


class SQLQueryProcessor:
    def __init__(self, filename, api_key):
        self.api_key: str = api_key
        self.operating_file: str = filename
        self.sqlinter_model: SQLinterModel = SQLinterModel()
        self.sql_searcher: SQLSearcher = None
        self.gpt: GPTModel = None
        self.original_queries: list = None
        self.parsed_queries: list = None
        self.queries_data: list[dict] = []
        self.queries_count: int = None

    def extract_queries(self):
        """Extract SQL queries using sql_searcher"""
        self.sql_searcher = SQLSearcher()
        searcher_results = self.sql_searcher.find_sql_in_file(
            self.operating_file)

        # Адаптируем формат данных под ожидаемый интерфейс
        self.original_queries = []
        for result in searcher_results:
            adapted_query = {
                'text': result['sql_query'],
                'start': result['start_pos'],
                'end': result['end_pos'],
                # Добавляем новые поля с информацией о позициях
                'start_line': result.get('start_line'),
                'start_column': result.get('start_column'),
                'end_line': result.get('end_line'),
                'end_column': result.get('end_column'),
                'line_content': result.get('line_content')
            }
            self.original_queries.append(adapted_query)

        self.parsed_queries = [query['text']
                               for query in self.original_queries]
        self.queries_count = len(self.parsed_queries)
        self._generate_queries_data()
        for i, item in enumerate(self.original_queries):
            self.queries_data[i].update({
                'query': item['text'],
                "start": item['start'],
                "end": item['end'],
                # Добавляем расширенную информацию о позициях
                "start_line": item.get('start_line'),
                "start_column": item.get('start_column'),
                "end_line": item.get('end_line'),
                "end_column": item.get('end_column'),
                "line_content": item.get('line_content')
            })

    def _generate_queries_data(self):
        """Generate queries data dictionary"""
        for i in range(self.queries_count):
            temp_query_data = query_data_template.copy()
            temp_query_data['id'] = i
            self.queries_data.append(temp_query_data)

    def process_with_gpt(self):
        """Process SQL queries using GPT model"""
        self.gpt = GPTModel(
            self.api_key, self.parsed_queries, self.queries_data)
        self.queries_data = self.gpt.get_queries

    def process_with_sqlinter(self):
        """Process SQL queries using SQLinter model"""
        for i, query in enumerate(self.parsed_queries):
            corrected_query = self.sqlinter_model.predict(query)
            self.queries_data[i].update({
                "correction": corrected_query,
            })

    def process(self):
        """Main processing pipeline"""
        self.extract_queries()
        self.process_with_gpt()
        self.process_with_sqlinter()

        # Убеждаемся, что вывод в UTF-8
        json_output = json.dumps(
            self.queries_data, indent=2, ensure_ascii=False)
        return json_output


def main():
    file_path = os.path.abspath(sys.argv[1])
    api_key = sys.argv[2]
    processor = SQLQueryProcessor(filename=file_path, api_key=api_key)
    print(processor.process())


if __name__ == "__main__":
    main()
