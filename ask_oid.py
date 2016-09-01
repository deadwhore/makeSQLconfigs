# функция для получения OID по IP


def ask_oid(ip, oid):
    # проверка, если там Unknown, то ничего не делаем
    if ip == 'Unknown':
        return False

    # для работы с snmpwalk Windows
    import subprocess

    # start MIB OID
    oid_start = oid

    # end MIB OID
    # получаем следующий по номеру OID
    oid_end = '.'.join(oid_start.split('.')[:-1]) + '.' + str(int(oid_start.split('.')[-1:][0]) + 1)

    # выполняем snmp запрос по айпи, стартовому oid, конечному oid
    try:
        snmp_result = subprocess.check_output([
            'snmpwalk/SnmpWalk.exe',
            '-v:2c',
            '-c:reworth',
            '-csv',
            '-r:' + ip,
            '-os:' + oid_start,
            '-op:' + oid_end
        ]).decode().strip()
    except Exception:
        return 'Error'

    timeout_snmp_result = '%Failed to get value of SNMP variable. Timeout.'

    # если был результат, то отрезаем лишнее и возвращаем
    if len(snmp_result) > 0:
        # если был таймаут, возвращаем слово offline
        if snmp_result == timeout_snmp_result:
            return 'offline'
        else:
            return snmp_result.split(',')[2]
    # если данный оид ничего не вернул, то возвращаем False
    else:
        return False


#print(ask_oid('10.19.1,44', '1.3.6.1.4.1.171.12.1.1.12'))