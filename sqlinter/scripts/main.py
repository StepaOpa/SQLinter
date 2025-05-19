import model
import sql_extractor
import os
import json
import sys

# api_key = os.getenv("OPENAI_API_KEY")
api_key = sys.argv[2]


def main():
    original_sqls = sql_extractor.main()
    sqlquerries = [query['text'] for query in sql_extractor.main()]
    gpt = model.GPTModel(api_key=api_key, sqlquerries=sqlquerries)
    gpt_response = gpt.queries
    for gpt_item, orig_query in zip(gpt_response, original_sqls):
        gpt_item.update({
            'start': orig_query.get('start'),
            'end': orig_query.get('end')
        })

    print(json.dumps(gpt_response, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    # print(main())
    main()
