# архивируем файлы

# для работы с Winrar
import subprocess

# для удаления использованных файлов
import os


def rar_it(sql_file, txt_file):
    try:
        sql_name = sql_file[:-7]
        subprocess.check_output([
            'winrar/rar.exe',
            'a',
            'old_sql/'+sql_name,
            'old_sql/*.sqlite'
        ])
        print('создан rar', sql_name)
        # удаляем
        os.remove('old_sql/'+sql_file)
    except Exception:
        print('Ошибка')

    try:
        txt_name = txt_file[:-4]
        subprocess.check_output([
            'winrar/rar.exe',
            'a',
            'old_txt/'+txt_name,
            'old_txt/*.txt'
        ])
        print('создан rar', txt_name)
        # удаляем
        os.remove('old_txt/'+txt_file)
    except Exception:
        print('Ошибка')

    return True


rar_it('configs_2016-06-28.sqlite', 'result_pars-2016-06-28.txt')