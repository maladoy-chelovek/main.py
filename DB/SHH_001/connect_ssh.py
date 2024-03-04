import paramiko


class SSHConnectingAndExec:
    """ Класс для установления соединения по SHH
    :argument data_dict - словарь состоящий из имени и значения
              command - команда которую необходимо выполнить
    """
    _data_dict = {
        'hostname': '',
        'port': 22,
        'username': '',
        'password': '',
    }

    def __init__(self, hostname: str, port: int, username: str, password: str, command: str) -> None:
        self.command = command
        self._data_dict['hostname'] = hostname
        self._data_dict['port'] = port
        self._data_dict['username'] = username
        self._data_dict['password'] = password

    def start_connection(self) -> str:
        # Создаем объект SSHClient
        client = paramiko.SSHClient()
        # Устанавливаем политику проверки хостов (в данном случае - игнорируем проверку)
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            # Подключаемся к удаленному серверу
            client.connect(self._data_dict['hostname'], self._data_dict['port'], self._data_dict['username'],
                           self._data_dict['password'], timeout=5)

            # Проверка удалось ли соединиться
            transport = client.get_transport().open_session()
            if transport is not None:
                transport.set_combine_stderr(True)
                transport.get_pty()

                # Выполняем команду на удаленном сервере
                print('\n\nВыполняю команду на удаленном сервере')
                transport.exec_command("sudo bash -c \"" + self.command + "\"")
                stdin = transport.makefile('wb', -1)
                stdout = transport.makefile('rb', -1)
                 # Ввод пароля
                stdin.write(self._data_dict['password'] + '\n')
                stdin.flush()

                # Читаем результат выполнения команды
                print('Читаем результат выполнения команды')
                return stdout.read().decode("utf-8")

            else:
                return 'Ошибка соединения'

        except Exception as e:
            print('Ошибка {error}'.format(error=e))

        finally:
            # Закрываем соединение
            client.close()
            print('Соединение закрыто')


# Устанавливаем параметры подключения
if __name__ == "__main__":
    my_connect = SSHConnectingAndExec(hostname='93.159.221.33', port=22, username='user', password='Zobrb',
                            command='ping 8.8.8.8 -c 5')
    my_connect.start_connection()