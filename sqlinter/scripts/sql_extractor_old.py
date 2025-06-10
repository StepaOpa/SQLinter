import re
import json
import sys
from typing import Dict, List


def editing(llist: list[str]):
    edited = []
    for i in range(0, len(llist)):
        stripped = llist[i]
        # stripped and '#' not in stripped and - убрал для того, чтобы можно было правильно вычислять позицию запроса.
        if not any(j in 'Ѓ°ґ±ЊЂѓ' for j in llist[i]):
            edited.append(stripped)
    return edited


def fill_parsed(lines: list):
    parsed = []
    stack = []
    # Создаём переменную, где будем хранить весь текст, то есть, код. Потом из него может будет узнать длину всего текста и в дальнейшем позицию запроса.
    symbols = ''
    value = ''
    for line in lines:
        linefake = line

        if ('=' in linefake) and (not stack) and not any(ttype in linefake for ttype in ['.execute(', '.executemany(', '.fetch(', '.read_sql(', '.copy_expert(']):
            # делает так, чтобы между var, = и value не было пробелов
            linefake = re.sub(r'\s*=\s*', '=', linefake)
            equal = linefake.index('=')
            var = linefake[:equal].replace(' ', '')
            start = 0
            if '"""' in linefake:

                start = len(symbols) + \
                    line.index('"""')  # определяем начало запроса

                qcount = linefake.count('"""')
                if qcount == 2:

                    secondq = line.replace(
                        '"""', "", 1)  # строка без первых кавычек
                    end = len(symbols) + secondq.index('"""') + \
                        5  # считаем конец запроса

                    woquote = linefake.replace('"""', "", 1)
                    woquoteindex = woquote.index('"""')+6
                    value += linefake[equal+1:woquoteindex]
                    parsed.append(
                        (var, value, {'text': value, 'start': start, 'end': end}))
                    value = ''
                else:
                    stack = ['"""']
                    if linefake[equal+1] != '(':
                        value += linefake[equal+1:]
                    else:
                        value += linefake[equal+2:]

            elif "'''" in linefake:
                start = len(symbols) + \
                    line.index("'''")  # определяем начало запроса

                qcount = linefake.count("'''")
                if qcount == 2:

                    secondq = line.replace(
                        "'''", "", 1)  # строка без первых кавычек
                    end = len(symbols) + secondq.index("'''") + \
                        5  # считаем конец запроса

                    woquote = linefake.replace("'''", "", 1)
                    woquoteindex = woquote.index("'''")+6
                    value += linefake[equal+1:woquoteindex]
                    parsed.append(
                        (var, value, {'text': value, 'start': start, 'end': end}))
                    value = ''
                else:
                    stack = ["'''"]
                    if linefake[equal+1] != '(':
                        value += linefake[equal+1:]
                    else:
                        value += linefake[equal+2:]

            elif '"' in linefake:
                start = len(symbols) + line.index('"')
                secondq = line.replace('"', "", 1)
                end = len(symbols) + secondq.index('"')+1

                woquote = linefake.replace('"', "", 1)
                woquoteindex = woquote.index('"')+2
                value += linefake[equal+1:woquoteindex]
                parsed.append(
                    (var, value, {'text': value, 'start': start, 'end': end}))
                value = ''

            elif "'" in linefake:
                start = len(symbols) + line.index("'")
                end = 0
                value = ''
                if line.count("'") > 2:
                    secondq = line.replace("'", "", line.count("'")-1)
                    end = len(symbols) + secondq.index("'") + line.count("'")

                    woquote = linefake.replace("'", "", line.count("'")-1)
                    woquoteindex = woquote.index("'")+line.count("'")
                    value += linefake[equal+1:woquoteindex]
                else:
                    secondq = line.replace("'", "", 1)
                    end = len(symbols) + secondq.index("'")

                    woquote = linefake.replace("'", "", 1)
                    woquoteindex = woquote.index("'")+2
                    value += linefake[equal+1:woquoteindex]
                parsed.append(
                    (var, value, {'text': value, 'start': start, 'end': end}))
                value = ''

        else:
            if stack:
                if '"""' in stack:
                    if '"""' in linefake:
                        if linefake != '"""':
                            stack = []

                            end = len(symbols) + line.index('"""')+2

                            woquoteindex = linefake.index('"""')+3
                            value += linefake[:woquoteindex]
                            parsed.append(
                                (var, value, {'text': value, 'start': start, 'end': end}))
                            value = ''
                        else:

                            end = len(symbols) + 3

                            stack = []
                            value += linefake
                            parsed.append(
                                (var, value, {'text': value, 'start': start, 'end': end}))
                            value = ''
                    else:
                        value += linefake

                elif "'''" in stack:
                    if "'''" in linefake:
                        if linefake != "'''":

                            end = len(symbols) + line.index("'''")+2

                            stack = []
                            woquoteindex = linefake.index("'''")+3
                            value += linefake[:woquoteindex]
                            parsed.append(
                                (var, value, {'text': value, 'start': start, 'end': end}))
                            value = ''
                        else:

                            end = len(symbols) + 3

                            stack = []
                            value += linefake
                            parsed.append(
                                (var, value, {'text': value, 'start': start, 'end': end}))
                            value = ''
                    else:
                        value += ' '+linefake
        symbols += line+'\n'

    return parsed


def extractor(lines):
    parsed = fill_parsed(lines)
    possible_sqls = []
    stack = []
    sql = ''
    symbols = ''
    for ttype in ['.execute(', '.executemany(', '.fetch(', '.read_sql(', '.copy_expert(']:
        for line in lines:
            if ttype in line:
                start = 0
                if '"""' in line and (line.index('(')+1 == line.index('"""')):

                    start = len(symbols) + line.index('"""') + \
                        (symbols.count('/n'))

                    quotes = line.count('"""')
                    if quotes == 2:
                        secondq = line.replace('"""', '', 1)
                        end = len(symbols) + secondq.index('"""')+6+1

                        firstquote = line.index('"""')
                        woquote = line.replace('"""', '', 1)
                        secondquote = woquote.index('"""')+6

                        sql = line[firstquote:secondquote]
                        possible_sqls.append(
                            {'text': sql, 'start': start, 'end': end})
                        sql = ''
                    else:
                        stack = ['"""']
                        firstquote = line.index('"""')
                        sql = line[firstquote:]

                elif "'''" in line and (line.index('(')+1 == line.index("'''")):

                    start = len(symbols) + line.index("'''") + \
                        (symbols.count('/n'))

                    quotes = line.count("'''")
                    if quotes == 2:

                        secondq = line.replace("'''", '', 1)
                        end = len(symbols) + secondq.index("'''")+6+1

                        firstquote = line.index("'''")
                        woquote = line.replace("'''", '', 1)
                        secondquote = woquote.index("'''")+6

                        sql = line[firstquote:secondquote]
                        possible_sqls.append(
                            {'text': sql, 'start': start, 'end': end})
                        sql = ''
                    else:
                        stack = ["'''"]
                        firstquote = line.index("'''")
                        sql = line[firstquote:]

                elif '"' in line and (line.index('(')+1 == line.index('"')):
                    start = len(symbols) + line.index('"') + \
                        (symbols.count('/n'))
                    secondq = line.replace('"', '', 1)
                    end = len(symbols) + secondq.index('"') + 2+1

                    firstquote = line.index('"')
                    woquote = line.replace('"', '', 1)
                    secondquote = woquote.index('"')+2
                    sql = line[firstquote:secondquote]
                    possible_sqls.append(
                        {'text': sql, 'start': start, 'end': end})
                    sql = ''

                elif "'" in line and (line.index('(')+1 == line.index("'")):
                    start = len(symbols) + line.index("'") + \
                        (symbols.count('/n'))
                    secondq = line.replace("'", '', 1)
                    end = len(symbols) + secondq.index("'") + 2+1

                    firstquote = line.index("'")
                    woquote = line.replace("'", '', 1)
                    secondquote = woquote.index("'")+2
                    sql = line[firstquote:secondquote]
                    possible_sqls.append(
                        {'text': sql, 'start': start, 'end': end})
                    sql = ''

                elif not any(quote in line[line.index('(')+1] for quote in ['"""', "'''", '"', "'"]):
                    if ',' not in line:
                        skobka1 = line.index('(')+1
                        skobka2 = line.index(')')
                        var = line[skobka1: skobka2]
                        for num, call in enumerate(parsed):
                            if call[0] == var:
                                possible_sqls.append(call[2])
                                parsed.pop(num)
                    else:
                        skobka1 = line.index('(')+1
                        zapytaya = line.index(',').replace(' ', '')
                        var = line[skobka1: zapytaya]
                        for num, call in enumerate(parsed):
                            if call[0] == var:
                                possible_sqls.append(call[2])
                                parsed.pop(num)
                        sql = ''
            else:
                if stack:
                    if '"""' in stack:
                        if '"""' in line:
                            if '"""' != line:

                                end = len(symbols) + line.index('"""')+3+1

                                stack = []
                                quote = line.index('"""')+3
                                sql += line[:quote]
                                possible_sqls.append(
                                    {'text': sql, 'start': start, 'end': end})
                                sql = ''
                            else:
                                end = len(symbols) + line.index('"""')+3+1

                                stack = []
                                sql += line
                                possible_sqls.append(
                                    {'text': sql, 'start': start, 'end': end})
                                sql = ''
                        else:
                            sql += line

                    elif "'''" in stack:
                        if "'''" in line:
                            if "'''" != line:
                                end = len(symbols) + line.index("'''")+3+1

                                stack = []
                                quote = line.index("'''")+3
                                sql += line[:quote]
                                possible_sqls.append(
                                    {'text': sql, 'start': start, 'end': end})
                                sql = ''
                            else:
                                end = len(symbols) + line.index("'''")+3+1

                                stack = []
                                sql += line
                                possible_sqls.append(
                                    {'text': sql, 'start': start, 'end': end})
                                sql = ''
                        else:
                            sql += line
            symbols += line+'\n'
    return possible_sqls


def main() -> List[Dict]:
    file_path = sys.argv[1]
    # with open('testpy copy.py', encoding='utf-8'). as f:
    with open(file_path, encoding='utf-8') as f:
        lines = editing(f.readlines())
        possible_sqls = extractor(lines)
        # parsed = fill_parsed(lines)
        # print(possible_sqls)
    return possible_sqls
    # return json.dumps(possible_sqls, ensure_ascii=False)


if __name__ == '__main__':
    possible_sqls = main()
    print(possible_sqls[0])
    # print(json.dumps(possible_sqls, ensure_ascii=False))
#     # print(json.dumps(possible_sqls, ensure_ascii=False))
