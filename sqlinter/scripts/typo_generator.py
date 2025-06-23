#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор опечаток для SQL ключевых слов.
Создает расширенный набор паттернов для обнаружения опечаток в SQL запросах.
"""

import json
import re
from itertools import combinations

class TypoGenerator:
    """Генератор различных типов опечаток для SQL ключевых слов."""
    
    def __init__(self):
        # Основные SQL ключевые слова для генерации опечаток
        self.sql_keywords = [
            'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'OUTER',
            'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'UNION', 'INTERSECT',
            'INTO', 'VALUES', 'SET', 'TABLE', 'INDEX', 'VIEW', 'DATABASE',
            'SCHEMA', 'COLUMN', 'CONSTRAINT', 'PRIMARY', 'FOREIGN', 'KEY',
            'UNIQUE', 'NOT', 'NULL', 'DEFAULT', 'CHECK', 'REFERENCES',
            'CASCADE', 'RESTRICT', 'BEGIN', 'COMMIT', 'ROLLBACK', 'TRANSACTION',
            'EXPLAIN', 'DESCRIBE', 'SHOW', 'USE', 'GRANT', 'REVOKE',
            'EXEC', 'EXECUTE', 'CALL', 'PROCEDURE', 'FUNCTION', 'TRIGGER',
            'CURSOR', 'FETCH', 'CLOSE', 'OPEN', 'DECLARE', 'CASE', 'WHEN',
            'THEN', 'ELSE', 'END', 'IF', 'EXISTS', 'IN', 'BETWEEN', 'LIKE',
            'IS', 'AND', 'OR', 'AS', 'DISTINCT', 'ALL', 'ANY', 'SOME'
        ]
        
        # Соседние клавиши на QWERTY клавиатуре
        self.keyboard_neighbors = {
            'Q': ['W', 'A'], 'W': ['Q', 'E', 'S'], 'E': ['W', 'R', 'D'],
            'R': ['E', 'T', 'F'], 'T': ['R', 'Y', 'G'], 'Y': ['T', 'U', 'H'],
            'U': ['Y', 'I', 'J'], 'I': ['U', 'O', 'K'], 'O': ['I', 'P', 'L'],
            'P': ['O', 'L'], 'A': ['Q', 'S', 'Z'], 'S': ['A', 'W', 'D', 'X'],
            'D': ['S', 'E', 'F', 'C'], 'F': ['D', 'R', 'G', 'V'],
            'G': ['F', 'T', 'H', 'B'], 'H': ['G', 'Y', 'J', 'N'],
            'J': ['H', 'U', 'K', 'M'], 'K': ['J', 'I', 'L'],
            'L': ['K', 'O', 'P'], 'Z': ['A', 'X'], 'X': ['Z', 'S', 'C'],
            'C': ['X', 'D', 'V'], 'V': ['C', 'F', 'B'], 'B': ['V', 'G', 'N'],
            'N': ['B', 'H', 'M'], 'M': ['N', 'J']
        }
        
        # Русская раскладка для QWERTY
        self.russian_layout = {
            'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н',
            'U': 'Г', 'I': 'Ш', 'O': 'Щ', 'P': 'З', 'A': 'Ф', 'S': 'Ы',
            'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л',
            'L': 'Д', 'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И',
            'N': 'Т', 'M': 'Ь'
        }
        
        self.generated_typos = set()
        self.typo_patterns = {}
    
    def generate_missing_char_typos(self, word):
        """Генерирует опечатки с пропущенными символами."""
        typos = []
        for i in range(len(word)):
            typo = word[:i] + word[i+1:]
            if len(typo) >= 2:  # Минимум 2 символа
                typos.append(typo)
        return typos
    
    def generate_transposition_typos(self, word):
        """Генерирует опечатки с перестановкой соседних символов."""
        typos = []
        for i in range(len(word) - 1):
            typo = word[:i] + word[i+1] + word[i] + word[i+2:]
            typos.append(typo)
        return typos
    
    def generate_extra_char_typos(self, word):
        """Генерирует опечатки с лишними символами."""
        typos = []
        # Удваиваем каждый символ
        for i in range(len(word)):
            typo = word[:i] + word[i] + word[i:]
            typos.append(typo)
        
        # Добавляем случайные символы из соседних клавиш
        for i in range(len(word)):
            char = word[i]
            if char in self.keyboard_neighbors:
                for neighbor in self.keyboard_neighbors[char]:
                    typo = word[:i] + char + neighbor + word[i+1:]
                    typos.append(typo)
        
        return typos
    
    def generate_substitution_typos(self, word):
        """Генерирует опечатки с заменой символов."""
        typos = []
        for i in range(len(word)):
            char = word[i]
            
            # Замена на соседние клавиши
            if char in self.keyboard_neighbors:
                for neighbor in self.keyboard_neighbors[char]:
                    typo = word[:i] + neighbor + word[i+1:]
                    typos.append(typo)
            
            # Замена на русскую раскладку
            if char in self.russian_layout:
                russian_char = self.russian_layout[char]
                typo = word[:i] + russian_char + word[i+1:]
                typos.append(typo)
        
        return typos
    
    def generate_common_mistakes(self, word):
        """Генерирует распространенные опечатки."""
        typos = []
        
        # Конкретные замены для часто встречающихся опечаток
        common_substitutions = {
            'SELECT': ['SELCT', 'SLECT', 'CELECT', 'GELECT', 'SEELCT'],
            'FROM': ['FORM', 'FRMO', 'FRON', 'FRIM'],
            'WHERE': ['WERE', 'WHRE', 'WHER', 'HWERE'],
            'INSERT': ['INSERTT', 'INSRT', 'INSER', 'INSERET'],
            'UPDATE': ['UPDAT', 'UPDAET', 'UPDTE', 'UPADTE'],
            'DELETE': ['DELET', 'DELTTE', 'DELE', 'DELTEE'],
            'CREATE': ['CREAT', 'CRAETE', 'CREAE', 'CEREAT'],
            'TABLE': ['TABEL', 'TABL', 'TABLEE', 'TBALE'],
            'VALUES': ['VALUE', 'VALEUS', 'VALES', 'VAULES'],
            'ORDER': ['ODER', 'ORER', 'ORDEER', 'ORDERR'],
            'GROUP': ['GRUP', 'GROPU', 'GRROUP', 'GOUP'],
            'HAVING': ['HAVNG', 'HAVNIG', 'HAVIG', 'HAVEING'],
            'LIMIT': ['LMIT', 'LIMT', 'LIMITT', 'LIIMT'],
            'JOIN': ['JION', 'JOINE', 'JOIIN', 'JOUN'],
            'INNER': ['INER', 'INNR', 'INEER', 'INNAR'],
            'LEFT': ['LEGT', 'LEFTT', 'LAFT', 'LEFY'],
            'RIGHT': ['RIGH', 'RIGHTT', 'RIHT', 'ROGHT'],
            'UNION': ['UNIO', 'UINON', 'UNNION', 'UION'],
            'INDEX': ['INDX', 'IDEX', 'INNDEX', 'INDEKS'],
            'ALTER': ['ALTR', 'ALEER', 'ALTEER', 'ALYER'],
            'DROP': ['DORP', 'DROPP', 'DEROP', 'DRAP']
        }
        
        if word in common_substitutions:
            typos.extend(common_substitutions[word])
        
        return typos
    
    def generate_case_variations(self, word):
        """Генерирует вариации регистра."""
        variations = []
        # Полностью строчные
        variations.append(word.lower())
        # Только первая заглавная
        variations.append(word.capitalize())
        # Смешанный регистр
        if len(word) > 2:
            variations.append(word[:2].upper() + word[2:].lower())
            variations.append(word[0].lower() + word[1:].upper())
        
        return variations
    
    def generate_all_typos_for_word(self, word):
        """Генерирует все типы опечаток для одного слова."""
        all_typos = set()
        
        # Различные типы опечаток
        all_typos.update(self.generate_missing_char_typos(word))
        all_typos.update(self.generate_transposition_typos(word))
        all_typos.update(self.generate_extra_char_typos(word))
        all_typos.update(self.generate_substitution_typos(word))
        all_typos.update(self.generate_common_mistakes(word))
        
        # Убираем исходное слово и слишком короткие варианты
        all_typos.discard(word)
        all_typos = {typo for typo in all_typos if len(typo) >= 2}
        
        # Добавляем вариации регистра для каждой опечатки
        final_typos = set()
        for typo in all_typos:
            final_typos.add(typo)
            final_typos.update(self.generate_case_variations(typo))
        
        return list(final_typos)
    
    def generate_context_patterns(self):
        """Генерирует контекстные паттерны для обнаружения SQL."""
        patterns = {}
        
        # Основные SQL команды с их контекстом
        sql_contexts = {
            'SELECT': ['FROM', 'WHERE', 'ORDER', 'GROUP', 'HAVING', 'LIMIT'],
            'INSERT': ['INTO', 'VALUES', 'SELECT'],
            'UPDATE': ['SET', 'WHERE'],
            'DELETE': ['FROM', 'WHERE'],
            'CREATE': ['TABLE', 'INDEX', 'VIEW', 'DATABASE'],
            'DROP': ['TABLE', 'INDEX', 'VIEW', 'DATABASE'],
            'ALTER': ['TABLE', 'ADD', 'DROP', 'MODIFY'],
            'WITH': ['SELECT', 'AS'],
            'SHOW': ['TABLES', 'DATABASES', 'COLUMNS'],
            'DESCRIBE': ['TABLE'],
            'EXPLAIN': ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        }
        
        for main_word, context_words in sql_contexts.items():
            main_typos = self.generate_all_typos_for_word(main_word)
            
            for context_word in context_words:
                context_typos = self.generate_all_typos_for_word(context_word)
                
                # Паттерн: опечатка в основном слове + правильное контекстное
                if main_typos:
                    pattern_key = f"{main_word}_typos_with_{context_word}"
                    pattern_value = rf'\b({"|".join(re.escape(typo) for typo in main_typos)})\b.*\b{context_word}\b'
                    patterns[pattern_key] = {
                        'pattern': pattern_value,
                        'description': f'Опечатки в {main_word} с контекстом {context_word}'
                    }
                
                # Паттерн: правильное основное слово + опечатка в контекстном
                if context_typos:
                    pattern_key = f"{main_word}_with_{context_word}_typos"
                    pattern_value = rf'\b{main_word}\b.*\b({"|".join(re.escape(typo) for typo in context_typos)})\b'
                    patterns[pattern_key] = {
                        'pattern': pattern_value,
                        'description': f'{main_word} с опечатками в {context_word}'
                    }
                
                # Паттерн: опечатки в обоих словах
                if main_typos and context_typos:
                    pattern_key = f"{main_word}_and_{context_word}_both_typos"
                    main_pattern = "|".join(re.escape(typo) for typo in main_typos[:10])  # Ограничиваем количество
                    context_pattern = "|".join(re.escape(typo) for typo in context_typos[:10])
                    pattern_value = rf'\b({main_pattern})\b.*\b({context_pattern})\b'
                    patterns[pattern_key] = {
                        'pattern': pattern_value,
                        'description': f'Опечатки в {main_word} и {context_word}'
                    }
        
        return patterns
    
    def generate_all_patterns(self):
        """Генерирует все паттерны опечаток."""
        print("Генерирую паттерны опечаток...")
        
        # Генерируем контекстные паттерны
        context_patterns = self.generate_context_patterns()
        
        # Генерируем простые паттерны для отдельных слов
        word_patterns = {}
        for word in self.sql_keywords:
            typos = self.generate_all_typos_for_word(word)
            if typos:
                pattern_key = f"{word}_typos"
                pattern_value = rf'\b({"|".join(re.escape(typo) for typo in typos)})\b'
                word_patterns[pattern_key] = {
                    'pattern': pattern_value,
                    'description': f'Опечатки в слове {word}',
                    'typos_count': len(typos)
                }
        
        all_patterns = {
            'context_patterns': context_patterns,
            'word_patterns': word_patterns,
            'metadata': {
                'total_context_patterns': len(context_patterns),
                'total_word_patterns': len(word_patterns),
                'generated_keywords': len(self.sql_keywords)
            }
        }
        
        return all_patterns
    
    def save_patterns_to_file(self, filename='sql_typo_patterns.json'):
        """Сохраняет сгенерированные паттерны в файл."""
        patterns = self.generate_all_patterns()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(patterns, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Паттерны сохранены в файл: {filename}")
        print(f"Статистика:")
        print(f"   - Контекстных паттернов: {patterns['metadata']['total_context_patterns']}")
        print(f"   - Словарных паттернов: {patterns['metadata']['total_word_patterns']}")
        print(f"   - Обработано ключевых слов: {patterns['metadata']['generated_keywords']}")
        
        return filename

def main():
    """Основная функция для генерации паттернов опечаток."""
    print("ГЕНЕРАТОР ПАТТЕРНОВ ОПЕЧАТОК SQL")
    print("=" * 50)
    
    generator = TypoGenerator()
    
    # Генерируем и сохраняем паттерны
    output_file = 'scripts/sql_typo_patterns.json'
    generator.save_patterns_to_file(output_file)
    
    print(f"\nГенерация завершена!")
    print(f"Файл с паттернами: {output_file}")
    print("\nДля использования в sql_searcher.py:")
    print("   Модифицируйте sql_searcher.py для загрузки паттернов из этого файла")

if __name__ == "__main__":
    main() 