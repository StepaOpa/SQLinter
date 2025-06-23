#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для поиска SQL запросов в Python файлах.
Находит как корректные, так и некорректные SQL запросы.
Возвращает абсолютные позиции первого и последнего символа каждого запроса.
"""

import ast
import re
import os
import sys
import json
from typing import List, Dict, Any, Optional, Tuple


class SQLSearcher:
    """Класс для поиска SQL запросов в Python файлах."""
    
    def __init__(self):
        # SQL ключевые слова для поиска
        self.sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'WITH', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL',
            'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT',
            'EXCEPT', 'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'SAVEPOINT',
            'BEGIN', 'END', 'TRANSACTION', 'INDEX', 'VIEW', 'TRIGGER', 'PROCEDURE',
            'FUNCTION', 'DECLARE', 'CURSOR', 'FETCH', 'CLOSE', 'OPEN', 'EXEC',
            'EXECUTE', 'CALL', 'SHOW', 'DESCRIBE', 'DESC', 'EXPLAIN', 'USE',
            'DATABASE', 'SCHEMA', 'TABLE', 'COLUMN', 'CONSTRAINT', 'PRIMARY',
            'FOREIGN', 'KEY', 'UNIQUE', 'NOT', 'NULL', 'DEFAULT', 'CHECK',
            'REFERENCES', 'ON', 'CASCADE', 'RESTRICT', 'SET', 'INTO', 'VALUES',
            'AS', 'DISTINCT', 'ALL', 'ANY', 'SOME', 'EXISTS', 'IN', 'BETWEEN',
            'LIKE', 'IS', 'AND', 'OR', 'CASE', 'WHEN', 'THEN', 'ELSE',
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'SUBSTRING', 'LENGTH',
            'UPPER', 'LOWER', 'TRIM', 'COALESCE', 'ISNULL', 'IFNULL'
        ]
        
        # Создаем регулярное выражение для поиска SQL запросов
        # Ищем строки, которые содержат SQL ключевые слова
        keywords_pattern = '|'.join(self.sql_keywords)
        self.sql_pattern = re.compile(
            rf'\b(?:{keywords_pattern})\b',
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        # Паттерн для более точного определения SQL запросов
        self.strong_sql_pattern = re.compile(
            r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|WITH|SHOW|DESCRIBE|EXPLAIN)\b',
            re.IGNORECASE | re.MULTILINE | re.DOTALL
        )
        
        # Загружаем расширенные паттерны опечаток
        self.typo_patterns = self._load_typo_patterns()
    
    def is_sql_query(self, text: str) -> bool:
        """
        Определяет, является ли текст SQL запросом.
        
        Args:
            text: Строка для проверки
            
        Returns:
            True, если строка содержит SQL запрос
        """
        if not text or not isinstance(text, str):
            return False
        
        # Убираем лишние пробелы и переводы строк
        cleaned_text = ' '.join(text.split())
        
        # Исключаем очевидные куски Python кода
        python_indicators = [
            '.execute(',   # cursor.execute(
            '.fetchall()', # cursor.fetchall()
            '.fetchone()', # cursor.fetchone()
            'cursor.',     # любое обращение к cursor
            'conn.',       # любое обращение к connection
            'import ',     # import statements
            'def ',        # function definitions
            'class ',      # class definitions
        ]
        
        for indicator in python_indicators:
            if indicator in cleaned_text.lower():
                return False
        
        # Специальная проверка для 'from' - только если это начало строки (import from)
        if cleaned_text.lower().startswith('from '):
            return False
        
        # Проверяем наличие сильных SQL ключевых слов
        if self.strong_sql_pattern.search(cleaned_text):
            return True
        
        # Проверяем наличие комбинации SQL ключевых слов
        sql_keywords_found = len(self.sql_pattern.findall(cleaned_text))
        
        # Если найдено 2 или более SQL ключевых слов, считаем это SQL запросом
        if sql_keywords_found >= 2:
            return True
        
        # Загружаем расширенные паттерны опечаток из файла
        if self._check_advanced_typo_patterns(cleaned_text):
            return True
        
        return False
    
    def _load_typo_patterns(self) -> Dict:
        """Загружает паттерны опечаток из JSON файла."""
        typo_file = os.path.join(os.path.dirname(__file__), 'sql_typo_patterns.json')
        
        if not os.path.exists(typo_file):
            return {'context_patterns': {}, 'word_patterns': {}}
        
        try:
            with open(typo_file, 'r', encoding='utf-8') as f:
                patterns = json.load(f)
            return patterns
        except Exception as e:
            return {'context_patterns': {}, 'word_patterns': {}}
    
    def _check_advanced_typo_patterns(self, text: str) -> bool:
        """Проверяет текст на соответствие расширенным паттернам опечаток."""
        if not self.typo_patterns:
            return False
        
        # Проверяем контекстные паттерны (приоритет - они более точные)
        context_patterns = self.typo_patterns.get('context_patterns', {})
        for pattern_name, pattern_data in context_patterns.items():
            pattern = pattern_data.get('pattern', '')
            if pattern:
                try:
                    if re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                        return True
                except re.error:
                    # Игнорируем некорректные паттерны
                    continue
        
        # Проверяем словарные паттерны (менее строгие)
        word_patterns = self.typo_patterns.get('word_patterns', {})
        word_matches = 0
        
        for pattern_name, pattern_data in word_patterns.items():
            pattern = pattern_data.get('pattern', '')
            if pattern:
                try:
                    if re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL):
                        word_matches += 1
                        # Если найдено 2 или более совпадений с разными словами, считаем SQL
                        if word_matches >= 2:
                            return True
                except re.error:
                    # Игнорируем некорректные паттерны
                    continue
        
        return False
    
    def find_sql_in_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Находит все SQL запросы в Python файле.
        
        Args:
            file_path: Путь к Python файлу
            
        Returns:
            Список словарей с информацией о найденных SQL запросов
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return []
        
        # Используем комбинированный подход: AST + прямой поиск
        sql_queries = []
        found_positions = set()  # Чтобы избежать дублирования
        
        # Сначала пробуем AST подход
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Str):
                    self._process_string_node_improved(node, content, sql_queries, node.s, found_positions)
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self._process_string_node_improved(node, content, sql_queries, node.value, found_positions)
                elif isinstance(node, ast.JoinedStr):
                    self._process_fstring_node_improved(node, content, sql_queries, found_positions)
        except SyntaxError:
            pass  # Продолжаем с резервным методом
        
        # Дополняем результаты прямым поиском (для случаев, которые AST мог пропустить)
        self._direct_string_search(content, sql_queries, found_positions)
        
        return sql_queries
    
    def _process_string_node_improved(self, node: ast.AST, content: str, sql_queries: List[Dict], string_value: str, found_positions: set):
        """Улучшенная обработка строкового узла AST."""
        if self.is_sql_query(string_value):
            positions = self._find_string_positions_improved(content, string_value, node.lineno, node.col_offset)
            for start_pos, end_pos in positions:
                # Корректируем позиции для содержимого строки
                content_start_pos, content_end_pos = self._get_string_content_positions(content, start_pos, end_pos, string_value)
                pos_key = (content_start_pos, content_end_pos)
                if pos_key not in found_positions:
                    found_positions.add(pos_key)
                    # Добавляем расширенную информацию о позициях
                    line_info = self._get_line_column_info(content, content_start_pos, content_end_pos)
                    
                    sql_queries.append({
                        'sql_query': string_value,
                        'start_pos': content_start_pos,
                        'end_pos': content_end_pos,
                        'line': node.lineno,
                        'column': node.col_offset,
                        # Добавляем точную информацию о строке и колонке
                        'start_line': line_info['start_line'],
                        'start_column': line_info['start_column'],
                        'end_line': line_info['end_line'], 
                        'end_column': line_info['end_column'],
                        'line_content': line_info['line_content']
                    })
    
    def _process_fstring_node_improved(self, node: ast.JoinedStr, content: str, sql_queries: List[Dict], found_positions: set):
        """Улучшенная обработка f-string узла AST."""
        fstring_content = self._reconstruct_fstring(node)
        
        if fstring_content and self.is_sql_query(fstring_content):
            positions = self._find_fstring_positions_improved(content, node.lineno, node.col_offset)
            for start_pos, end_pos in positions:
                # Для f-strings используем более точную коррекцию позиций
                content_start_pos, content_end_pos = self._get_fstring_content_positions(content, start_pos, end_pos)
                pos_key = (content_start_pos, content_end_pos)
                if pos_key not in found_positions:
                    found_positions.add(pos_key)
                    # Добавляем расширенную информацию о позициях для f-strings
                    line_info = self._get_line_column_info(content, content_start_pos, content_end_pos)
                    
                    sql_queries.append({
                        'sql_query': fstring_content,
                        'start_pos': content_start_pos,
                        'end_pos': content_end_pos,
                        'line': node.lineno,
                        'column': node.col_offset,
                        # Добавляем точную информацию о строке и колонке
                        'start_line': line_info['start_line'],
                        'start_column': line_info['start_column'],
                        'end_line': line_info['end_line'], 
                        'end_column': line_info['end_column'],
                        'line_content': line_info['line_content']
                    })
    
    def _reconstruct_fstring(self, node: ast.JoinedStr) -> str:
        """Восстанавливает содержимое f-string из AST."""
        parts = []
        for value in node.values:
            if isinstance(value, ast.Str):
                parts.append(value.s)
            elif isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                # Для старых версий Python без ast.unparse
                try:
                    if hasattr(ast, 'unparse'):
                        parts.append(f"{{{ast.unparse(value.value)}}}")
                    else:
                        # Простое представление для совместимости
                        parts.append("{variable}")
                except:
                    parts.append("{variable}")
        return ''.join(parts)
    
    def _find_string_positions(self, node: ast.AST, content: str, string_value: str) -> Tuple[Optional[int], Optional[int]]:
        """Находит абсолютные позиции строки в файле."""
        lines = content.split('\n')
        
        # Пытаемся найти точную позицию строки
        if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            line_idx = node.lineno - 1
            col_offset = node.col_offset
            
            if line_idx < len(lines):
                # Вычисляем абсолютную позицию начала
                start_pos = sum(len(line) + 1 for line in lines[:line_idx]) + col_offset
                
                # Ищем конец строки
                line_content = lines[line_idx]
                string_in_line = self._find_string_in_line(line_content, col_offset, string_value)
                
                if string_in_line:
                    end_pos = start_pos + len(string_in_line) - 1
                    return start_pos, end_pos
        
        return None, None
    
    def _find_fstring_positions(self, node: ast.JoinedStr, content: str) -> Tuple[Optional[int], Optional[int]]:
        """Находит абсолютные позиции f-string в файле."""
        lines = content.split('\n')
        
        if hasattr(node, 'lineno') and hasattr(node, 'col_offset'):
            line_idx = node.lineno - 1
            col_offset = node.col_offset
            
            if line_idx < len(lines):
                # Вычисляем абсолютную позицию начала
                start_pos = sum(len(line) + 1 for line in lines[:line_idx]) + col_offset
                
                # Для f-strings ищем от f" до закрывающей кавычки
                line_content = lines[line_idx][col_offset:]
                match = re.search(r'f["\'].*?["\']', line_content, re.DOTALL)
                
                if match:
                    end_pos = start_pos + match.end() - 1
                    return start_pos, end_pos
        
        return None, None
    
    def _find_string_in_line(self, line: str, col_offset: int, string_value: str) -> Optional[str]:
        """Находит строку в строке кода."""
        # Ищем строку, начинающуюся с кавычки
        for quote in ['"', "'", '"""', "'''"]:
            if line[col_offset:].startswith(quote):
                # Ищем закрывающую кавычку
                end_quote_pos = line.find(quote, col_offset + len(quote))
                if end_quote_pos != -1:
                    return line[col_offset:end_quote_pos + len(quote)]
        
        return None
    
    def _find_string_positions_improved(self, content: str, string_value: str, approx_line: int, approx_col: int) -> List[Tuple[int, int]]:
        """Улучшенный поиск позиций строки в содержимом файла."""
        positions = []
        
        # Экранируем специальные символы в строке для поиска  
        escaped_value = re.escape(string_value)
        
        # Ищем строку в окрестности указанной позиции (более точный поиск)
        lines = content.split('\n')
        if approx_line - 1 < len(lines):
            # Ищем в окрестности указанной строки
            search_start = max(0, approx_line - 3)
            search_end = min(len(lines), approx_line + 3)
            
            # Соединяем строки для поиска
            search_lines = lines[search_start:search_end]
            search_content = '\n'.join(search_lines)
            
            # Вычисляем смещение для корректировки позиций
            offset = sum(len(lines[i]) + 1 for i in range(search_start))
            
            # Паттерны для поиска с разными типами кавычек
            quote_patterns = [
                rf'"""({escaped_value})"""',     # Тройные двойные кавычки
                rf"'''({escaped_value})'''",     # Тройные одинарные кавычки  
                rf'"({escaped_value})"',         # Двойные кавычки
                rf"'({escaped_value})'",         # Одинарные кавычки
            ]
            
            for pattern in quote_patterns:
                for match in re.finditer(pattern, search_content, re.DOTALL):
                    # Корректируем позиции с учетом смещения
                    start_pos = offset + match.start()
                    end_pos = offset + match.end() - 1
                    positions.append((start_pos, end_pos))
        
        return positions
    
    def _find_fstring_positions_improved(self, content: str, approx_line: int, approx_col: int) -> List[Tuple[int, int]]:
        """Улучшенный поиск позиций f-string в содержимом файла."""
        positions = []
        
        # Паттерны для поиска различных типов f-strings
        fstring_patterns = [
            r"f'''(.*?)'''",    # f'''...'''
            r'f"""(.*?)"""',    # f"""..."""
            r"f'([^'\\]*(?:\\.[^'\\]*)*)'",    # f'...'
            r'f"([^"\\]*(?:\\.[^"\\]*)*)"',    # f"..."
        ]
        
        # Ищем в окрестности указанной позиции  
        lines = content.split('\n')
        if approx_line - 1 < len(lines):
            # Берем контекст вокруг указанной строки
            search_start = max(0, approx_line - 3)
            search_end = min(len(lines), approx_line + 3)
            
            # Соединяем строки для поиска
            search_lines = lines[search_start:search_end]
            search_content = '\n'.join(search_lines)
            
            # Вычисляем смещение для корректировки позиций
            offset = sum(len(lines[i]) + 1 for i in range(search_start))
            
            for pattern in fstring_patterns:
                for match in re.finditer(pattern, search_content, re.DOTALL):
                    # Корректируем позиции с учетом смещения
                    start_pos = offset + match.start()
                    end_pos = offset + match.end() - 1
                    positions.append((start_pos, end_pos))
        
        return positions
    
    def _get_string_content_positions(self, content: str, full_start: int, full_end: int, string_content: str) -> Tuple[int, int]:
        """
        Определяет позиции содержимого строки (без кавычек).
        
        Args:
            content: Полное содержимое файла
            full_start: Начальная позиция строки с кавычками
            full_end: Конечная позиция строки с кавычками
            string_content: Содержимое строки без кавычек
            
        Returns:
            Tuple с позициями начала и конца содержимого строки
        """
        # Получаем полную строку с кавычками
        full_string = content[full_start:full_end + 1]
        
        # Определяем тип кавычек и их длину
        if full_string.startswith('"""') or full_string.startswith("'''"):
            quote_len = 3
        elif full_string.startswith('"') or full_string.startswith("'"):
            quote_len = 1
        else:
            # Если не удается определить кавычки, возвращаем исходные позиции
            return full_start, full_end
        
        # Позиции содержимого = позиции строки + длина открывающих кавычек
        content_start = full_start + quote_len
        content_end = full_end - quote_len
        
        return content_start, content_end
    
    def _get_line_column_info(self, content: str, start_pos: int, end_pos: int) -> Dict[str, Any]:
        """
        Получает точную информацию о строке и колонке для заданных позиций.
        
        Args:
            content: Полное содержимое файла
            start_pos: Начальная абсолютная позиция
            end_pos: Конечная абсолютная позиция
            
        Returns:
            Словарь с информацией о строке и колонке
        """
        lines = content.split('\n')
        
        # Находим строку и колонку для начальной позиции
        current_pos = 0
        start_line = 1
        start_column = 0
        
        for line_num, line in enumerate(lines, 1):
            line_end = current_pos + len(line)
            if start_pos <= line_end:
                start_line = line_num
                start_column = start_pos - current_pos
                break
            current_pos = line_end + 1  # +1 для символа \n
        
        # Находим строку и колонку для конечной позиции
        current_pos = 0
        end_line = 1
        end_column = 0
        
        for line_num, line in enumerate(lines, 1):
            line_end = current_pos + len(line)
            if end_pos <= line_end:
                end_line = line_num
                end_column = end_pos - current_pos
                break
            current_pos = line_end + 1  # +1 для символа \n
        
        # Получаем содержимое строки для отладки
        line_content = lines[start_line - 1] if start_line <= len(lines) else ""
        
        return {
            'start_line': start_line,
            'start_column': start_column,
            'end_line': end_line,
            'end_column': end_column,
            'line_content': line_content,
            # Добавляем альтернативные позиции через line+column
            'alt_start_pos': self._line_column_to_pos(content, start_line, start_column),
            'alt_end_pos': self._line_column_to_pos(content, end_line, end_column)
        }
    
    def _line_column_to_pos(self, content: str, line: int, column: int) -> int:
        """
        Преобразует номер строки и колонки в абсолютную позицию.
        
        Args:
            content: Полное содержимое файла
            line: Номер строки (1-based)
            column: Номер колонки (0-based)
            
        Returns:
            Абсолютная позиция в файле
        """
        lines = content.split('\n')
        if line <= 0 or line > len(lines):
            return 0
        
        # Суммируем длины всех предыдущих строк + символы \n
        pos = sum(len(lines[i]) + 1 for i in range(line - 1))
        pos += column
        
        return pos
    
    def _get_fstring_content_positions(self, content: str, full_start: int, full_end: int) -> Tuple[int, int]:
        """
        Определяет позиции содержимого f-string (без f" и ").
        
        Args:
            content: Полное содержимое файла
            full_start: Начальная позиция f-string
            full_end: Конечная позиция f-string
            
        Returns:
            Tuple с позициями начала и конца содержимого f-string
        """
        # Получаем полную f-string
        full_fstring = content[full_start:full_end + 1]
        
        # Определяем тип кавычек и корректируем позиции
        if full_fstring.startswith("f'''") or full_fstring.startswith('f"""'):
            # f'''...''' или f"""..."""
            content_start = full_start + 4  # f''' или f"""
            content_end = full_end - 3      # ''' или """
        elif full_fstring.startswith("f'") or full_fstring.startswith('f"'):
            # f'...' или f"..."
            content_start = full_start + 2  # f' или f"
            content_end = full_end - 1      # ' или "
        else:
            # Если не удается определить, возвращаем исходные позиции
            return full_start, full_end
        
        return content_start, content_end
    
    def _direct_string_search(self, content: str, sql_queries: List[Dict], found_positions: set):
        """Прямой поиск строковых литералов в тексте файла."""
        # Паттерны для поиска различных типов строковых литералов
        # Порядок важен: сначала более специфичные (тройные кавычки), потом обычные
        string_patterns = [
            r'"""(.*?)"""',  # Тройные двойные кавычки
            r"'''(.*?)'''",  # Тройные одинарные кавычки
            r'"([^"\\]*(?:\\.[^"\\]*)*)"',  # Двойные кавычки
            r"'([^'\\]*(?:\\.[^'\\]*)*)'",  # Одинарные кавычки
        ]
        
        # Отслеживаем уже обработанные диапазоны, чтобы избежать перекрытий
        processed_ranges = []
        
        for pattern in string_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                start_pos = match.start()
                end_pos = match.end() - 1
                string_content = match.group(1)
                
                # Проверяем, не пересекается ли с уже обработанными диапазонами
                is_overlapping = any(
                    start_pos < proc_end and end_pos > proc_start 
                    for proc_start, proc_end in processed_ranges
                )
                
                if not is_overlapping and self.is_sql_query(string_content):
                    # Корректируем позиции, чтобы они указывали на содержимое строки, а не на кавычки
                    content_start_pos, content_end_pos = self._get_string_content_positions(content, start_pos, end_pos, string_content)
                    pos_key = (content_start_pos, content_end_pos)
                    
                    if pos_key not in found_positions:
                        found_positions.add(pos_key)
                        processed_ranges.append((start_pos, end_pos))
                        
                        # Добавляем расширенную информацию о позициях для прямого поиска
                        line_info = self._get_line_column_info(content, content_start_pos, content_end_pos)
                        
                        sql_queries.append({
                            'sql_query': string_content,
                            'start_pos': content_start_pos,
                            'end_pos': content_end_pos,
                            'line': content[:start_pos].count('\n') + 1,
                            'column': len(content[:start_pos].split('\n')[-1]),
                            # Добавляем точную информацию о строке и колонке
                            'start_line': line_info['start_line'],
                            'start_column': line_info['start_column'],
                            'end_line': line_info['end_line'], 
                            'end_column': line_info['end_column'],
                            'line_content': line_info['line_content']
                        })
    
    def _fallback_search(self, content: str) -> List[Dict[str, Any]]:
        """Резервный метод поиска SQL в тексте (для обратной совместимости)."""
        sql_queries = []
        found_positions = set()
        self._direct_string_search(content, sql_queries, found_positions)
        return sql_queries
    
    def search_in_directory(self, directory: str, recursive: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Ищет SQL запросы во всех Python файлах в директории.
        
        Args:
            directory: Путь к директории
            recursive: Искать ли в поддиректориях
            
        Returns:
            Словарь с результатами поиска по файлам
        """
        results = {}
        
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        sql_queries = self.find_sql_in_file(file_path)
                        if sql_queries:
                            results[file_path] = sql_queries
        else:
            for file in os.listdir(directory):
                if file.endswith('.py'):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        sql_queries = self.find_sql_in_file(file_path)
                        if sql_queries:
                            results[file_path] = sql_queries
        
        return results


def main():
    """Основная функция для запуска скрипта."""
    if len(sys.argv) < 2:
        print("Использование: python sql_searcher.py <путь_к_файлу_или_директории> [--recursive]")
        sys.exit(1)
    
    path = sys.argv[1]
    recursive = '--recursive' in sys.argv or '-r' in sys.argv
    
    searcher = SQLSearcher()
    
    if os.path.isfile(path):
        # Поиск в одном файле
        if path.endswith('.py'):
            results = searcher.find_sql_in_file(path)
            print(f"Найдено SQL запросов в файле {path}: {len(results)}")
            for i, query in enumerate(results, 1):
                print(f"\n{i}. SQL запрос (строка {query.get('line', 'N/A')}):")
                print(f"   Позиция: {query['start_pos']}-{query['end_pos']}")
                print(f"   Запрос: {repr(query['sql_query'][:100])}...")
        else:
            print("Файл должен иметь расширение .py")
    
    elif os.path.isdir(path):
        # Поиск в директории
        results = searcher.search_in_directory(path, recursive)
        total_queries = sum(len(queries) for queries in results.values())
        
        print(f"Найдено SQL запросов в {len(results)} файлах: {total_queries}")
        
        for file_path, queries in results.items():
            print(f"\nФайл: {file_path}")
            print(f"   Найдено запросов: {len(queries)}")
            
            for i, query in enumerate(queries, 1):
                print(f"   {i}. Строка {query.get('line', 'N/A')}, позиция {query['start_pos']}-{query['end_pos']}")
                print(f"      Запрос: {repr(query['sql_query'][:80])}...")
    
    else:
        print(f"Путь {path} не существует")
        sys.exit(1)


if __name__ == "__main__":
    main()
