import re


def editing(llist: list[str]):
    fake = []
    for i in range(0, len(llist)):
        stripped = llist[i].strip()
        if stripped and stripped[0]!='#' and not any(j in 'Ѓ°ґ±ЊЂѓ' for j in llist[i]):
            fake.append(llist[i].replace('\n',''))
    return fake


def sql_extractor():
    with open('test.py') as f:
        lines = editing(f.readlines())
        possible_sql = []
        sql = ''
        stack = []

        for line in lines:
            
            if 'execute(' in line or 'fetch(' in line or 'read_sql' in line:
                start = 0
                if 'execute(' in line:
                    start = line.index('execute(')+8

                elif 'fetch(' in line:
                    start = line.index('fetch(')+6
                    
                elif 'read_sql(' in line:
                    start = line.index('read_sql(')+9

                if (line[start] in "'" or line[start] in '"'):
                        if not stack:
                            stack = ['(']
                        
                        for ch in range(start, len(line)):
                            if not stack:
                                break
                                
                            if line[ch] == '(':
                                stack.append('(')
                                sql += '('
                            elif line[ch] == ')':
                                stack.pop()
                                if not stack:
                                    sql = sql.replace('"','')
                                    sql = sql.replace("'","")
                                    possible_sql.append(sql)
                                    sql = ''
                                    break
                            elif stack and line[ch] not in '()':
                                sql += line[ch]

            elif stack:
                        for ch in line:
                            if ch == '(':
                                stack.append('(')
                                sql += '('
                            elif ch == ')':
                                stack.pop()
                                if not stack:
                                    sql = sql.replace('"','')
                                    sql = sql.replace("'","")

                                    possible_sql.append(sql[:len(sql)]+')')
                                    sql = ''
                                    break
                            elif stack and ch not in '()':
                                sql += ch

            elif any(word in line.upper() for word in ['SELECT','INSERT','UPDATE','DELETE','CREATE','ALTER','DROP','AUTO_INCREMENT','TEXT NOT NULL', "PRIMARY KEY"]):
                        for ch in line:
                            if ch == '(':
                                stack.append('(')
                                sql += '('
                            elif ch == ')':
                                stack.pop()
                                sql += ')'
                                if not stack:
                                    possible_sql.append(sql[:len(sql)])
                                    sql = ''
                                    break
                            else:
                                sql += ch                 

        return possible_sql                           
