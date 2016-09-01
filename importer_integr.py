# -*- coding: utf-8 -*-
# author: Maxim Pisarenko <pisarenkomakzzz@yandex.ru>
# date: 16.06.16
# script version: 0.2

import sqlite3


import datetime


# импортируем функцию опроса MIB OID по IP
from ask_oid import ask_oid as ask_oid


# функция работы с .ods таблицами
def ods_dismember(ods_source):
        # разбираем .ods на строки

        # импорт этой чудовищной библиотеки odfpy, которая умеет работать с .ods
        from odf.opendocument import load
        # from odf.opendocument import Spreadsheet
        from odf.text import P
        from odf.table import TableRow, TableCell
        # пишем, с каким файлом работаем
        print(ods_source)
        # в этом списке будем хранить все строки, каждый элемент - ещё один список с содержимым строки
        row_list = []
        # сюда будем помещать данные с одной строки
        row_list_element = []
        # счётчик строк
        row_number = 0
        # номер ячейки
        cell_number = 0
        # хранилище файлика
        doc = load(ods_source).spreadsheet
        # получаем строку из .ods
        rows = doc.getElementsByType(TableRow)
        # начинаем строки обрабатывать
        for row in rows:
            cell_number = 0
            row_number += 1
            if row_number % 500 == 0:
                print('processing', row_number, 'rows')
            # раскладываем строку по ячейкам
            cells = row.getElementsByType(TableCell)
            # по-очереди начинаем тыкаться в ячейки и проверять что там есть
            for cell in range(len(cells)):
                cell_number += 1
                # кидаем в отдельную переменную внутренности ячейки, "Р" здесь, видимо текст или даже параграф, хз
                all_data = cells[cell].getElementsByType(P)
                # если нам удалось что-то выцепить из ячейки, уже можно иметь с этим дело
                if len(all_data) > 0:
                    # добавляем в маленький списочек данные, этот список содержит одну строку
                    row_list_element.append(str(all_data[0]))
                elif cell_number == 1 and len(all_data) == 0:
                    break
                else:
                    row_list_element.append('')

            # в этот элемент list засовываем список, содержащий одну строку, проверяем, что элементов больше одного
            if len(row_list_element) > 1 and not 'Комментарий' in row_list_element:
                row_list.append(row_list_element[:])
            row_list_element.clear()

        # убираем первую строку, если она состоит из описания столбцов
        if len(row_list) > 0 and ('ССЫЛКИ' in row_list[0] or 'Дуплекс' in row_list[0]):
            row_list.remove(row_list[0])
        return row_list


# идём по выдержке из ods и выбираем из него по-очереди оборудование,
# будем отдельно обрабатывать каждое оборудование отдельно
def split_ods_config(result_file, ods_config):
    # список с отдельным коммутатором
    switch_list = []
    # флаг для контроля нового коммутатора
    new_switch = False
    # идём по списку со всеми коммутаторами
    for row in ods_config:
        # если это новый титул свича
        if 'DES' in row[0] or 'DGS' in row[0] or 'AT' in row[0] or 'DMC' in row[0] \
                or 'isco' in row[0] or 'Netgear' in row[0]:
            # это мы идём не в первый раз
            if new_switch is True:
                ip, switch_hostname, switch_address, switch_vendor, edited_ports_list = ods_extract_parsing(switch_list)
                result_file.write(ip + '  ' + switch_hostname + '  ' + switch_address + '  ' + switch_vendor)
                result_file.write('\n')
                sql_insert_new_switch(ip, switch_hostname, switch_address, switch_vendor, edited_ports_list)
                for ports in edited_ports_list:
                    try:
                        result_file.write('\t' + '  '.join(ports) + '\n')
                    except UnicodeEncodeError:
                        result_file.write('\t *** LibreOffice autocorrector unicode error ***\n')
                switch_list.clear()
            # ЭТО МЫ ИДЁМ В ПЕРВЫЙ РАЗ
            else:
                new_switch = True
        switch_list.append(row[:])
    ip, switch_hostname, switch_address, switch_vendor, edited_ports_list = ods_extract_parsing(switch_list)
    result_file.write(ip + '  ' + switch_hostname + '  ' + switch_address + '  ' + switch_vendor)
    result_file.write('\n')
    sql_insert_new_switch(ip, switch_hostname, switch_address, switch_vendor, edited_ports_list)
    for ports in edited_ports_list:
        result_file.write('\t' + '  '.join(ports) + '\n')


    # сделаем парсинг каждой железки, нам нужно получить с него:
    # 1) домен и шлюз
    # 2) из заголовка адрес и хостнейм
    # 3) проверяем есть ли DES/AT/DGS/DMC в титуле - это у нас будет модель оборудования
    # 5) нам нужены названия портов (на случай, если там 1/e10), подписи, вланы, комментарии
def ods_extract_parsing(ods_config):
    switch_model = ''

    ip = ods_config[0][1]
    if ip == '':
        ip = 'Unknown'
    title = ods_config[0][0]
    # здесь вырезаем адрес из скобочек, т.к. скобочки нам попадаются дважды - берём только первую и отрезаем первый
    # символ - там скобка открывается. Та, которая закрывается уже отрезал .split
    switch_address = title.split(')')[0][1:]
    # в имя хоста кладём то же самое, но второй кусок строки - начиная от закрытой скобки за минус
    # первый символ - пробел
    switch_hostname = title.split(')')[1][1:]
    # если есть rdtc.ru в найденном
    if 'rdtc.ru' in switch_hostname:
        # получаем много лишнего в конце отрезка, отрезаем по доменному имени, а потом прилепливаем его сзади
        switch_hostname = switch_hostname.split('rdtc.ru')[0] + 'rdtc.ru'
    # а если нет, делим по пробелу
    else:
        switch_hostname = switch_hostname.split(' ')[0] + '.rdtc.ru'

    # модель оборудования

    if 'DES-3' in ods_config[0][0]:
        switch_model = 'DES-3200'
    # D-link DGS-3620-28
    elif 'DGS-3620' in ods_config[0][0]:
        switch_model = 'DGS-3620'
    # D-link DGS-3120-24TC
    elif 'DGS-3120' in ods_config[0][0]:
        switch_model = 'DGS-3120'
    # D-link DGS-3100-24TG
    elif 'DGS-3100' in ods_config[0][0]:
        switch_model = 'DGS-3100'
    # AlliedTelesys AT-8000S/16
    elif 'AT-8000' in ods_config[0][0]:
        switch_model = 'AT-8000'
    # D-Link DMC
    elif 'DMC-100' in ods_config[0][0]:
        switch_model = 'DMC-1000'
    # Cisco
    elif 'isco' in ods_config[0][0]:
        switch_model = 'Cisco'

    # получаем список списков со всеми портами, без лишних столбцов, для DMC всего два поля - порт и подписка
    edited_ports_list = []
    temp_list = []
    # print(switch_model)
    if switch_model == 'DMC-1000':
        for ports in ods_config[1:]:
            temp_list.append(ports[0])
            temp_list.append(ports[1])
            temp_list.append('')
            edited_ports_list.append(temp_list[:])
            temp_list.clear()
    else:
        # print(ods_config)
        for ports in ods_config[1:]:
            temp_list.append(ports[0])
            # print(ports[0])
            temp_list.append(ports[2])
            # print(ports[2])
            temp_list.append(ports[5])
            # print(ports[5])
            edited_ports_list.append(temp_list[:])
            temp_list.clear()

    return ip, switch_hostname, switch_address, switch_model, edited_ports_list


# заносим в базу данные: айпи, хостнейм, адрес, вендор, порты 100, порты 1G, общее кол-во портов, и далее
def sql_insert_new_switch(ip, switch_hostname, switch_address, switch_vendor, ports):
    # связь с базой данных
    global cursor

    # проверяем, были ли узлы с таким же IP
    cursor.execute('SELECT priority FROM Switch WHERE ip_switch = ? ', (ip, ))
    find_ip = cursor.fetchall()
    priority = 0
    # если были ещё узлы с таким IP
    if len(find_ip) > 0:
        # здесь ищем самый высокий приоритет. это связано с тем, что может быть несколько узлов с одним IP, а может быть
        # что какие-то из этих записей удалены. В таком случае приоритет не просто последовательные 0, 1, 2, ..., а
        # 0, 1, 2, 4, 6, ...
        for x in find_ip:
            if x[0] > priority:
                priority = x[0]
        priority += 1
    cursor.execute('''INSERT INTO Switch (ip_switch, priority) VALUES (?, ?)''', (ip, priority))

    # теперь нам нужен ID только что вставленного IP
    cursor.execute('SELECT id_switch FROM Switch WHERE ip_switch = ? AND priority = ?', (ip, priority))
    id_sw_sql = cursor.fetchone()[0]

    # вставляем остальные данные в другие таблицы

    # вставляем адрес
    cursor.execute('''INSERT INTO Address (id_switch, switch_hostname, address) VALUES (?, ?, ?)''',
                   (id_sw_sql, switch_hostname, switch_address))

    # вставляем описание железки
    cursor.execute('''INSERT INTO Hardware (id_switch, model, ports) VALUES (?, ?, ?)''',
                   (id_sw_sql, switch_vendor, len(ports)))

    # вставляем порты!
    port_number = 1
    for port in ports:
        # print(port)
        cursor.execute('''INSERT INTO Ports (id_switch, number, name, description, vlan) VALUES (?, ?, ?, ?, ?)''',
                       (id_sw_sql, port_number, port[0], port[1], port[2]))
        port_number += 1

    # вставляем серийный номер по oid=1.3.6.1.4.1.171.12.1.1.12, он работает только для D-link, но AT нам и не нужны -
    # у них с последней прошивкой затёрты серийные номера
    oid = '1.3.6.1.4.1.171.12.1.1.12'
    result_oid = ask_oid(ip, oid)
    if result_oid is not False:
        cursor.execute('''UPDATE Hardware SET serial=? WHERE id_switch=?''', (result_oid, id_sw_sql))


# нам нужно получить список .ods файлов с адресами
def get_address():
    # данная библиотека умеет работать с директориями и файлами
    import os
    # берём содержимое папки генератором списков, все файлы, у которых встречается .ods в названии
    list_of_ods = [files for files in os.listdir('Коммутаторы\\') if '.ods' in files]
    return ['Коммутаторы\\' + elem for elem in list_of_ods]


# -=-=-=-=-=-=-=- начало программы -=-=-=-=-=-=-=-

def start_importing():
    today = str(datetime.date.today())

    # подключаем базу данных
    sql_file = 'old_sql/configs_' + today + '.sqlite'
    connection = sqlite3.connect(sql_file)
    global cursor
    cursor = connection.cursor()

    # пересоздаём базу данных, удаляем старыe таблицы, создаём новые
    cursor.executescript('''
    DROP TABLE IF EXISTS Switch;
    DROP TABLE IF EXISTS Address;
    DROP TABLE IF EXISTS Ports;
    DROP TABLE IF EXISTS Hardware;

    CREATE TABLE Switch (
        id_switch INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        ip_switch TEXT,
        priority INTEGER
    );

    CREATE TABLE Address (
        id_switch INTEGER NOT NULL PRIMARY KEY UNIQUE,
        switch_hostname TEXT,
        city TEXT,
        address TEXT,
        special  TEXT
    );

    CREATE TABLE Ports (
        id_switch     INTEGER NOT NULL,
        number INTEGER,
        name  TEXT,
        description  TEXT,
        vlan  TEXT,
        mode  TEXT,
        speed  INTEGER,
        hardware  TEXT,
        comments  TEXT
    );

    CREATE TABLE Hardware (
        id_switch     INTEGER NOT NULL PRIMARY KEY UNIQUE,
        vendor  TEXT,
        model  TEXT,
        revision  TEXT,
        stack INTEGER,
        ports INTEGER,
        mac  TEXT,
        serial  TEXT,
        date_of_created DATE,
        date_of_removed DATE
    )
    ''')
    print('DB created')

    # здесь храним название файлов .ods
    config_files = get_address()

    # открываем фаил для записи результатов парсинга
    txt_file = 'old_txt/result_pars-' + today + '.txt'
    with open(txt_file, 'w') as result_file:
        # идём по улицам
        for street in config_files:
            # новый список, там храним результат функции разделения .ods
            list_of_ods_rows = ods_dismember(street)

            # result_file.write('Новая улица ' + street + '\n')
            print('Новая улица ' + street[12:-4])

            # используем функцию для парсинга и внесения в sql данных
            split_ods_config(result_file, list_of_ods_rows)

    print('END!')
    connection.commit()

    return today + '.sqlite', today + '.txt'


