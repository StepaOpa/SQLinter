from GPT_model import GPTModel
import sql_extractor
import os
import json
import sys
from SQLinterModel import SQLinterModel

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
    def __init__(self, api_key):
        self.api_key: str = api_key
        self.sqlinter_model: SQLinterModel = SQLinterModel()
        self.gpt: GPTModel = None
        self.original_queries: list = None
        self.parsed_queries: list = None
        self.queries_data: list[dict] = []
        self.queries_count: int = None
        print('initialized')

    def extract_queries(self):
        """Extract SQL queries using sql_extractor"""
        self.original_queries = sql_extractor.main()
        print(self.original_queries)
        self.parsed_queries = [query['text']
                               for query in self.original_queries]
        self.queries_count = len(self.parsed_queries)
        self._generate_queries_data()
        for i, item in enumerate(self.original_queries):
            self.queries_data[i].update({
                'query': item['text'],
                "start": item['start'],
                "end": item['end']
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
        return json.dumps(self.queries_data, indent=2, ensure_ascii=False)


def main():
    file_path = os.path.abspath(sys.argv[1])
    api_key = sys.argv[2]
    processor = SQLQueryProcessor(api_key)
    print(processor.process())


if __name__ == "__main__":
    main()
