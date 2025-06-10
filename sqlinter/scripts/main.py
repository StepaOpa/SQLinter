from GPT_model import GPTModel
import sql_extractor
import os
import json
import sys
from SQLinterModel import SQLinterModel

query_data = {
    "id": int,
    "query": str,
    "verdict": str,
    "reason": str,
    "corrected": str,
    "start": None,
    "end": None
}


class SQLQueryProcessor:
    def __init__(self, api_key):
        self.api_key: str = api_key
        self.sqlinter_model: SQLinterModel = SQLinterModel()
        self.gpt: GPTModel = None
        self.original_sqls: list = None
        self.parsed_sql_queries: list = None
        self.corrected_queries: list = None
        self.gpt_response = None
        self.queries_data: list[dict] = []
        self.queries_count: int = None

    def extract_queries(self):
        """Extract SQL queries using sql_extractor"""
        self.original_sqls = sql_extractor.main()
        self.parsed_sql_queries = [query['text']
                                   for query in self.original_sqls]
        self.queries_count = len(self.parsed_sql_queries)
        self.generate_queries_data()
        # TODO
        # сделать чтоб спаршенный sql запрос записался в queries_data под своим индексом

    def generate_queries_data(self):
        """Generate queries data dictionary"""
        for i in range(self.queries_count):
            temp_query_data = query_data
            temp_query_data['id'] = i
            self.queries_data.append(temp_query_data)

    def process_with_sqlinter(self):
        """Process SQL queries using SQLinter model"""
        for sql_query in self.parsed_sql_queries:
            corrected_query = self.sqlinter_model.predict(sql_query)
            # TODO
            # переписать код модели так чтоб она принимала queries_data и возвращала его заполненным

    def merge_metadata(self):
        """Merge original query metadata with GPT responses"""
        for gpt_item, orig_query in self.gpt_response:
            gpt_item.update({
                'start': orig_query.get('start'),
                'end': orig_query.get('end')
            })

    def process(self):
        """Main processing pipeline"""
        self.extract_queries()
        self.generate_queries_data()

        return json.dumps(self.gpt_response, indent=2, ensure_ascii=False)


def main():
    api_key = sys.argv[2]
    processor = SQLQueryProcessor(api_key)
    print(processor.process())


if __name__ == "__main__":
    main()
