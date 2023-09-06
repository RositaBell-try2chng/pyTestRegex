import sqlite3
import requests as req
import re

def addBadLink(all, key, value):
    '''
        оставляем только плохие домены, по которым ответ приходит либо с редиректом либо с ошибкой в запросе
    '''
    try:
        resFamCode = req.head(f'http://{value}')
        if (resFamCode.status_code >= 300 or resFamCode.status_code < 500):
            raise Exception('bad status code')
    except:
        if (all.get(key, None) is None):
            all[key] = []
        all[key].append(value)


def getSplArray(arr):
    '''
        разбиваем домен по точкам, составляем лист из листов с возможными вариантами написания домена
    '''
    allArr = []
    i = 0
    for one in arr:
        spl = one.split('.')
        spl.reverse()
        for i in range(len(spl)):
            if (i > len(allArr) - 1):
                allArr.append([])
            if (spl[i] not in allArr[i]):
                allArr[i].append(spl[i])
    return allArr

def getPoolStr(arr):
    '''
        Вспомогательная функция. формирует строку для вставки в регулярку с выбором из нескольких возможных значений
    '''
    res = ''
    for el in arr:
        res += f"({el})?"
    res = '(' + res + '){1}'
    return res

def setRegex(all, cursor, key, con):
    '''
        составляем регулярку и записываем в базу.
        заказчик дает нам домен 2го уровня + еще 1 уровень как минимум нужен для регулярки, чтобы не отсеивать абсолютно все домены клиента. поэтому первые 3 элемента должны быть выбором из множества.
        далее если количество вариантов меньше 10, то тоже вставляем выбор из списка, иначе - любая последовательность символов.
    '''
    if (len(all) <= 2):
        return
    i = 3
    first = getPoolStr(all[0])
    second = getPoolStr(all[1])
    third = getPoolStr(all[2])
    toSet = third + '[.]' + second + '[.]' + first
    while i < len(all):
        toSet = '[.]?' + toSet
        if len(all[i]) < 10:
            nextOne = getPoolStr(all[i]) + '?'
        else:
            nextOne = '(.+)?'
        toSet = nextOne + toSet
        i += 1
    cursor.execute("INSERT INTO rules SELECT '" + str(key) + "', '" + toSet + "'")
    con.commit()


def main():
    '''
        main func
        1. коннектимся к базе
        2. достаем домены
        3. в all записываем только нужный
        4. для каждого project_id составляем лист из листов возможных вариантов, составляем регулярку и кладем в базу.
    '''
    con = sqlite3.connect('domains.db')
    cursor = con.cursor()
    cursor.execute('SELECT * FROM domains;')
    all = {}
    for one in cursor.fetchall():
        addBadLink(all, one[0], one[1])
    for key in all.keys():
        allArr = getSplArray(all[key])
        setRegex(allArr, cursor, key, con)
    cursor.close()

    

if __name__ == '__main__':
    main()