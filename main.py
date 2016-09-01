# -*- coding: utf-8 -*-
# author: Maxim Pisarenko <pisarenkomakzzz@yandex.ru>
# date: 23.06.16
# script version: 0.1

# Основной скрипт, служит для копирования фаилов из сетевой шары поближе,
# запуск модулей для импорта данных из ods. в sqlite, добавление туда серийных номеров D-link.
# В будущем, архивирование фаилов

# данная библиотека умеет работать с директориями и файлами
import os

# данная библотека умеет копировать удобно
import shutil

# преобразование в sql
import importer_integr

# модуль для архивирования и удаления
import rar


# нам нужно получить список .ods файлов с адресами и удалить из них лишние
def get_address(source_dir):
    # берём содержимое папки генератором списков, все файлы, у которых встречается .ods и нет ~lock в названии
    list_of_ods = [files for files in os.listdir(source_dir) if '.ods' in files and '~lock' not in files]

    # отфильтруем лишние файлы .ods из списска, шаблоны, офисные узлы и прочее
    filtering = ['1 Ссылки.ods', '1 Шаблоны.ods', '1Тест.ods', 'Офис-стойка.ods']
    for delete in filtering:
        if delete in list_of_ods:
            list_of_ods.remove(delete)
    return list_of_ods


# -=-=-=-=-=-=-=- начало программы -=-=-=-=-=-=-=-


# папка с файлами коммутаторов
source_dir = '//192.168.10.11/files/Documents/Отдел эксплуатации/Служебная документация/Коммутаторы'
ods_addresses = get_address(source_dir)

# сюда будем копировать для работы
copy_dir = 'Коммутаторы'

# очистим локальную папку с коммутаторами
del_counter = 0
local_comms = os.listdir(copy_dir+'/')
for elem in local_comms:
    del_counter += 1
    os.remove(copy_dir+'/'+elem)
print(del_counter, 'файлов удалено')

# копируем файлы .ods из сетевой шары в локальную папку
copy_counter = 0
for copy in ods_addresses:
    copy_counter += 1
    shutil.copyfile(source_dir+'/'+copy, copy_dir+'/'+copy)

print(copy_counter, 'файлов скопировано')

# импортируем данные в sqlite, берём название sqlite файла
sql_file, txt_file = importer_integr.start_importing()

print('импортинг завершён')

# архивируем и удаляем результаты работы
rar.rar_it(sql_file, txt_file)




