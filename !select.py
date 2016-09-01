# данная библиотека умеет работать с директориями и файлами
import os

# для работы с sqllite
import sqlite3

# смотрим какие файлы есть в архивах
list_of_sql = [files for files in os.listdir('old_sql/') if '.sqlite' in files]

# самый свежий фаил
earliest = (max(list_of_sql))

# подключаем базу данных
connection = sqlite3.connect('old_sql/' + earliest)
cursor = connection.cursor()

# простенький интерфейс вывода данных
while True:
    print('-=' * 14)
    print('Введите IP адрес коммутатора')
    ip_switch = input('> ')
    # проверка, если просто Enter нажат
    if len(ip_switch) == 0:
        continue
    # нам надо получить самый последний коммутатор, потому что на адресе могли быть замены
    cursor.execute('SELECT id_switch, MAX(priority) FROM Switch WHERE ip_switch=?', (ip_switch, ))
    # получили с наивысшим приоритетом и отрезали приоритет, оставив только идентификатор свича
    id_switch = cursor.fetchall()[0][0]
    # теперь, собственно, получаем всё об этом свиче
    cursor.execute(
        'SELECT Switch.ip_switch, Address.switch_hostname, Address.address from Switch join Address '
        'WHERE Address.id_switch=Switch.id_switch AND Switch.id_switch=?', (id_switch, ))
    print(cursor.fetchall())
    cursor.execute(
        'SELECT Hardware.model, Hardware.ports, Hardware.serial from Hardware WHERE id_switch=?', (id_switch, ))
    print(cursor.fetchall())
    cursor.execute(
        'SELECT Ports.name, Ports.description, Ports.vlan FROM Ports JOIN Switch ON '
        'Switch.id_switch = Ports.id_switch AND Switch.id_switch=?', (id_switch, ))
    ports_list = cursor.fetchall()
    for port in ports_list:
        print(port)

    print()
