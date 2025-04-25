import re

def editing(llist: list[str]):
    edited = []
    for i in range(0, len(llist)):
        stripped = llist[i]
        if stripped and '#' not in stripped and not any(j in 'Ѓ°ґ±ЊЂѓ' for j in llist[i]):
            edited.append(stripped)
    return edited


def fill_parsed(lines: list):
    parsed = {}
    stack = []
    value = ''
    for line in lines:
        linefake=line
        if ('=' in linefake) and (not stack) and not any(ttype in linefake for ttype in ['.execute(','.executemany(','.fetch(','.read_sql(','.copy_expert(']):
            linefake = re.sub(r'\s*=\s*', '=', linefake) #делает так, чтобы между var, = и value не было пробелов
            equal = linefake.index('=')
            var = linefake[:equal]
            if '"""' in linefake:
                qcount = linefake.count('"""')
                if qcount == 2:
                    woquote = linefake.replace('"""',"",1) 
                    woquoteindex = woquote.index('"""')+6 
                    value += linefake[equal+1:woquoteindex] 
                    parsed[var]=value
                    value = ''
                else:
                    stack = ['"""']
                    if linefake[equal+1]!='(':
                        value += linefake[equal+1:]
                    else:
                        value += linefake[equal+2:]

            elif "'''" in linefake:
                qcount = linefake.count("'''")
                if qcount == 2:
                    woquote = linefake.replace("'''","",1) 
                    woquoteindex = woquote.index("'''")+6 
                    value += linefake[equal+1:woquoteindex] 
                    parsed[var]=value
                    value = ''
                else:
                    stack = ["'''"]
                    if linefake[equal+1]!='(':
                        value += linefake[equal+1:]
                    else:
                        value += linefake[equal+2:]
            
            elif '"' in linefake:
                woquote = linefake.replace('"',"",1) 
                woquoteindex = woquote.index('"')+2 
                value += linefake[equal+1:woquoteindex] 
                parsed[var]=value
                value = ''

            elif "'" in linefake:
                woquote = linefake.replace("'","",1) 
                woquoteindex = woquote.index("'")+2 
                value += linefake[equal+1:woquoteindex] 
                parsed[var]=value
                value = ''

        else:
            if stack:
                if '"""' in stack:
                    if '"""' in linefake:
                        if linefake != '"""':
                            stack = []
                            woquoteindex = linefake.index('"""')+3
                            value += linefake[:woquoteindex] 
                            parsed[var]=value
                            value = ''
                        else:
                            stack = []
                            value += linefake
                            parsed[var]=value
                            value = ''
                    else:
                        value += linefake

                elif "'''" in stack:
                    if "'''" in linefake:
                        if linefake != "'''":
                            stack = [] 
                            woquoteindex = linefake.index("'''")+3
                            value += linefake[:woquoteindex] 
                            parsed[var]=value
                            value = ''
                        else:
                            stack = []
                            value += linefake
                            parsed[var]=value
                            value = ''
                    else:
                        value += ' '+linefake

    return parsed


def extractor(lines):
    parsed = fill_parsed(lines)
    possible_sqls = []
    stack = []
    sql = ''
    for ttype in ['.execute(','.executemany(','.fetch(','.read_sql(','.copy_expert(']:
        for line in lines:
            if ttype in line:
                if '"""' in line and (line.index('(')+1==line.index('"""')):
                    quotes = line.count('"""')
                    if quotes == 2:
                        firstquote = line.index('"""')
                        woquote = line.replace('"""','',1)
                        secondquote = woquote.index('"""')+6
                        
                        sql = line[firstquote:secondquote]
                        possible_sqls.append(sql)
                        sql = ''
                    else:
                        stack = ['"""']
                        firstquote = line.index('"""')
                        sql = line[firstquote:]


                elif "'''" in line and (line.index('(')+1==line.index("'''")):
                    quotes = line.count("'''")
                    if quotes == 2:
                        firstquote = line.index("'''")
                        woquote = line.replace("'''",'',1)
                        secondquote = woquote.index("'''")+6
                        
                        sql = line[firstquote:secondquote]
                        possible_sqls.append(sql)
                        sql = ''
                    else:
                        stack = ["'''"]
                        firstquote = line.index("'''")
                        sql = line[firstquote:]

                elif '"' in line and (line.index('(')+1==line.index('"')):
                    firstquote = line.index('"')
                    woquote = line.replace('"','',1)
                    secondquote = woquote.index('"')+2
                    sql = line[firstquote:secondquote]
                    possible_sqls.append(sql)
                    sql = ''

                elif "'" in line and (line.index('(')+1==line.index("'")):
                    firstquote = line.index("'")
                    woquote = line.replace("'",'',1)
                    secondquote = woquote.index("'")+2
                    sql = line[firstquote:secondquote]
                    possible_sqls.append(sql)
                    sql = ''

                elif not any(quote in line[line.index('(')+1] for quote in ['"""',"'''",'"',"'"]):
                    if ',' not in line:
                        skobka1 = line.index('(')+1
                        skobka2 = line.index(')')
                        var = line[skobka1: skobka2]
                        sql = parsed[var]
                        try:
                            sql = parsed[var]
                            possible_sqls.append(sql)
                        except KeyError:
                            print(f'Ключ "{var}" не найден.')
                        sql = ''
                    else:
                        skobka1 = line.index('(')+1
                        zapytaya = line.index(',')
                        var = line[skobka1: zapytaya]    
                        try:
                            sql = parsed[var]
                            possible_sqls.append(sql)
                        except KeyError:
                            print(f'Ключ "{var}" не найден.')
                        sql = ''
            else:
                if stack:
                    if '"""' in stack:
                        if '"""' in line:
                            if '"""' != line:
                                stack = []
                                quote = line.index('"""')+3
                                sql += line[:quote]
                                possible_sqls.append(sql)
                                sql = ''
                            else:
                                stack = []
                                sql += line
                                possible_sqls.append(sql)
                                sql = ''
                        else:
                            sql += line

                    elif "'''" in stack:
                        if "'''" in line:
                            if "'''" != line:
                                stack = []
                                quote = line.index("'''")+3
                                sql += line[:quote]
                                possible_sqls.append(sql)
                                sql = ''
                            else:
                                stack = []
                                sql += line
                                possible_sqls.append(sql)
                                sql = ''
                        else:
                            sql += line

    return possible_sqls


def main():
    with open('test2.py') as f:
        lines = editing(f.readlines())
        possible_sqls = extractor(lines)
        parsed = fill_parsed(lines)
    return possible_sqls


spisok = main()
for i in spisok:
    print(i)
