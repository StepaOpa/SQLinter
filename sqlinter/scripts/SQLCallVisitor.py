#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример скрипта, который ищет потенциально исполняемые SQL-запросы в Python-коде
и выводит уникальные результаты в виде списка словарей:
[
  {
    'text': <строка запроса>,
    'start': <число, начало в символах>,
    'end': <число, конец в символах>
  },
  ...
]

Основные этапы:
1. Парсим Python-код модулем ast.
2. Собираем строки, которые выглядят как SQL, и сохраняем их в переменных.
3. Когда встречаем вызов методов, содержащих в названии 'execute', проверяем, не передаётся ли туда
   либо строка SQL напрямую, либо ранее сохранённая переменная.
4. Выдаём итоговый список уникальных словарей — строк, которые действительно исполняются.

Запуск:
    python new_extractor3.py путь_к_файлу_с_кодом.py
"""

import ast
import sys
import os
import difflib


def get_absolute_position(file_text, lineno, col_offset):
    """
    Преобразовать (lineno, col_offset) в абсолютный индекс в тексте.
    lineno базируется на 1, col_offset — на 0.
    """
    lines = file_text.splitlines(True)
    if lineno <= 0 or lineno > len(lines):
        return 0
    return sum(len(lines[i]) for i in range(lineno - 1)) + col_offset


class SQLCallVisitor(ast.NodeVisitor):
    SQL_KEYWORDS = ("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER")

    def __init__(self, file_content=""):
        super().__init__()
        # Словарь: имя_переменной -> список словарей {'text':..., 'start':..., 'end':...}
        self.sql_variables = {}
        # Список реально используемых (исполняемых) запросов
        self.executed_queries = []

        # Сырой текст файла для вычисления позиций
        self.file_content = file_content


    def visit_Assign(self, node):
        """
        Обработка присвоений: если строка похоже на SQL, запомним её за переменной.
        """
        # Определим, каким переменным присваивается значение
        targets = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                targets.append(target.id)

        extracted = self._extract_string_info(node.value)
        if extracted and self._maybe_sql(extracted["text"]):
            for tname in targets:
                self.sql_variables.setdefault(tname, []).append(extracted)

        self.generic_visit(node)


    def visit_Call(self, node):
        """Находим вызовы методов, где в названии есть 'execute', и извлекаем SQL."""
        func_name = self._get_func_full_name(node.func)
        if func_name and any(i in func_name.lower() for i in ['execute', 'executemany', 'fetch', 'read_sql', 'copy_expert']):
            for arg in node.args:
                # Если это сразу строка
                extracted = self._extract_string_info(arg)
                if extracted and self._maybe_sql(extracted["text"]):
                    self.executed_queries.append(extracted)
                elif isinstance(arg, ast.Name):
                    var_name = arg.id
                    if var_name in self.sql_variables:
                        for partial_sql in self.sql_variables[var_name]:
                            if self._maybe_sql(partial_sql["text"]):
                                self.executed_queries.append(partial_sql)
        self.generic_visit(node)


    def _maybe_sql(self, text):
        """Проверка на ключевые слова SQL с учетом возможных опечаток."""
        upper_text = text.upper()
        # Точное совпадение
        for keyword in self.SQL_KEYWORDS:
            if keyword in upper_text:
                return True
        # Фаззи-проверка по отдельным словам
        words = upper_text.split()
        for keyword in self.SQL_KEYWORDS:
            for word in words:
                if difflib.SequenceMatcher(None, word, keyword).ratio() > 0.8:
                    return True
        return False


    def _get_func_full_name(self, func):
        """Собираем полное имя функции (например, 'conn.cursor.execute')."""
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            parent_name = self._get_func_full_name(func.value)
            return f"{parent_name}.{func.attr}" if parent_name else func.attr
        return None


    def _extract_string_info(self, node):
        """
        Пытаемся определить строку и её границы относительно всего файла.
        Возвращаем:
        {
          'text': <строка>,
          'start': <абсолютный индекс>,
          'end': <абсолютный индекс>
        }
        или None.
        """
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {
                "text": node.value,
                "start": get_absolute_position(self.file_content, node.lineno, node.col_offset),
                "end": get_absolute_position(self.file_content, node.end_lineno, node.end_col_offset)
            }
        elif isinstance(node, ast.JoinedStr):
            # f-строка
            text_parts = []
            for val in node.values:
                if isinstance(val, ast.FormattedValue):
                    text_parts.append("{...}")
                elif isinstance(val, ast.Constant) and isinstance(val.value, str):
                    text_parts.append(val.value)
            return {
                "text": "".join(text_parts),
                "start": get_absolute_position(self.file_content, node.lineno, node.col_offset),
                "end": get_absolute_position(self.file_content, node.end_lineno, node.end_col_offset)
            }
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            # Конкатенация (string1 + string2)
            left_info = self._extract_string_info(node.left)
            right_info = self._extract_string_info(node.right)
            if left_info and right_info:
                return {
                    "text": left_info["text"] + right_info["text"],
                    "start": min(left_info["start"], right_info["start"]),
                    "end": max(left_info["end"], right_info["end"])
                }
        return None


    def process_file(self, filename):
        if not os.path.exists(filename):
            # print(f"Файл '{filename}' не найден.")  # убираем отладочный вывод
            return []

        with open(filename, "r", encoding="utf-8") as f:
            file_content = f.read()

        tree = ast.parse(file_content)
        self.file_content = file_content
        self.visit(tree)

        # Извлекаем только уникальные словари
        unique_executed_queries = []
        seen = set()
        for q in self.executed_queries:
            # Преобразуем словарь в кортеж, чтобы можно было проверять в set
            key = (q["text"], q["start"], q["end"])
            if key not in seen:
                unique_executed_queries.append(q)
                seen.add(key)
        
        return unique_executed_queries


def main():
    if len(sys.argv) < 2:
        print("Использование: python new_extractor3.py <путь_к_файлу_с_кодом.py>")
        sys.exit(1)
    filename = sys.argv[1]
    visitor = SQLCallVisitor("")  # Создаем экземпляр с пустым содержимым
    visitor.process_file(filename)


if __name__ == "__main__":
    main()
