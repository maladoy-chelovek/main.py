import sys
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
from ssh_check import Ui_Dialog
import sqlite3
import os
import re
import connect_ssh
import datetime

class window(QDialog):
    """ Класс отображает на экране таблицу из бд и выполняет некоторый код
        :arguments:  __path_db отвечает за абсолютный путь к БД
    """
    __path_db = os.path.abspath('sshsql.db')
    __cur_data = {
        'name': '',
        'id': 0,
        'ip': '',
        'port': 22,
        'login': '',
        'passw': ''
    }

    __status_button = {
        'hack_rf': 1,
        'generation': 1
    }
    __list_id = []
    __list_commands = []

    def __init__(self):
        """
            Место, где происходит инициализация действий
        """
        super(window, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Settings
        header = self.ui.tableWidget.horizontalHeader()
        header.setStyleSheet("font-family: Times New Roman; font-size: 18px;")  # Задаем шрифт и размер заголовков
        self.ui.tableWidget.setHorizontalHeaderLabels(['Адрес', 'IP', 'Port', 'Login', 'Пароль'])  # Имена заголовков
        self.load_data_sql()  # Загрузка БД в таблицу
        self.load_commands()
        self.ui.tableWidget.itemClicked.connect(self.oneclick)  # Реакция на одиночный клик
        self.ui.save_but.clicked.connect(self.save_data)  # Вызов функции при нажатии на кнопку Сохранить
        self.ui.add_but.clicked.connect(self.add_data)  # Вызов функции при нажатии на кнопку Добавить
        self.ui.cancel_but.clicked.connect(self.startposition)  # Вызов функции при нажатии на кнопку Отмена
        self.ui.del_but.clicked.connect(self.delete_data)  # Вызов функции при нажатии на кнопку Удалить
        self.startposition()  # Первоначальные значения для LineEdit
        # Settings

        # Monitoring
        header = self.ui.tableWidget_Monitoring.horizontalHeader()
        header.setStyleSheet("font-family: Times New Roman; font-size: 18px;")  # Задаем шрифт и размер заголовков
        self.ui.tableWidget_Monitoring.setHorizontalHeaderLabels(['Адрес', 'IP', 'Port', 'Login', 'Пароль',
                                                                  'Статус Трансляции', 'Статус Генерации'])
        # Имена заголовков

        self.ui.tableWidget_Monitoring.itemClicked.connect(self.one_monitclick)  # Реакция на клик
        self.ui.transl_but.clicked.connect(self.start_hackrf)   # Вызов функции при нажатии на кнопку Стоп Трансляции
        self.ui.generator_but.clicked.connect(self.start_generate)  # Вызов функции при нажатии на кнопку Стоп Генерации
        self.ui.status_but.clicked.connect(self.status_serv)
        # Monitoring

    # Settings__________________________________________________________________________________________________________
    def oneclick(self):
        """
            Реакция на одинарный клик. Подставляем значения из таблицы в lineEdit. И вычисления текущего id
            позиции
        """
        for item in self.ui.tableWidget.selectedItems():
            try:
                self.__cur_data['id'] = self.__list_id[item.row()]
                self.ui.Name_lineEdit.setText(self.ui.tableWidget.item(item.row(), 0).text())  # Столбец Name
                self.ui.Ip_lineEdit_2.setText(self.ui.tableWidget.item(item.row(), 1).text())  # Столбец IP
                self.ui.Port_lineEdit_3.setText(self.ui.tableWidget.item(item.row(), 2).text())  # Столбец Port
                self.ui.Login_lineEdit_4.setText(self.ui.tableWidget.item(item.row(), 3).text())  # Столбец Login
                self.ui.Passw_lineEdit_5.setText(self.ui.tableWidget.item(item.row(), 4).text())  # Столбец Password
            except Exception as e:
                self.ui.plainTextEdit_Memo.appendPlainText('Ошибка записи данных в LineEdit {error}'.format(error=e))

    def startposition(self):
        """
            Получаем первоначальные значения для LineEdit
        """
        try:
            self.__cur_data['id'] = self.__list_id[0]
            self.ui.Name_lineEdit.setText(self.ui.tableWidget.item(0, 0).text())  # Столбец Name
            self.ui.Ip_lineEdit_2.setText(self.ui.tableWidget.item(0, 1).text())  # Столбец IP
            self.ui.Port_lineEdit_3.setText(self.ui.tableWidget.item(0, 2).text())  # Столбец Port
            self.ui.Login_lineEdit_4.setText(self.ui.tableWidget.item(0, 3).text())  # Столбец Login
            self.ui.Passw_lineEdit_5.setText(self.ui.tableWidget.item(0, 4).text())  # Столбец Password

            if (self.ui.tableWidget_Monitoring.item(0, 0) is not None and
                    self.ui.tableWidget_Monitoring.item(0, 1) is not None):
                self.ui.label_cur_dev.setText('Текущее устройство: ' +
                                              self.ui.tableWidget_Monitoring.item(0, 0).text() + ' ' +
                                              self.ui.tableWidget_Monitoring.item(0, 1).text())

                self.__cur_data['name'] = self.ui.tableWidget_Monitoring.item(0, 0).text()  # Запись текущего имени
                self.__cur_data['ip'] = self.ui.tableWidget_Monitoring.item(0, 1).text()    # Запись текущего IP
                self.__cur_data['port'] = int(self.ui.tableWidget_Monitoring.item(0, 2).text())  # Запись текущего Порта
                self.__cur_data['login'] = self.ui.tableWidget_Monitoring.item(0, 3).text()  # Запись текущего Логина
                self.__cur_data['passw'] = self.ui.tableWidget_Monitoring.item(0, 4).text()  # Запись текущего Пароля
        except Exception as e:
            self.ui.plainTextEdit_Memo.appendPlainText('Нет данных для записи первоначальных значений в '
                                                       'LineEdit или в Lable {error}'.format(error=e))

    def load_data_sql(self):
        """
            Данная функция осуществляет подключение к БД. И через метод SELECT
            публикует эти данные в TableWidget
        """
        with sqlite3.connect(self.__path_db) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute('SELECT id, name, ip, port, login, password FROM main')
                conn.commit()
                result = cursor.fetchall()  # Результат запроса

                if result is not None:
                    self.ui.tableWidget.setRowCount(len(result))  # Устанавливаем кол-во строк для вывода
                    row_index = 0
                    self.__list_id = []
                    for row in result:
                        # Заполнение tableWidget
                        self.__list_id.append(row[0])  # Запись Id оборудование в список
                        self.ui.tableWidget.setItem(row_index, 0, QtWidgets.QTableWidgetItem(row[1]))  # Name
                        self.ui.tableWidget.setItem(row_index, 1, QtWidgets.QTableWidgetItem(row[2]))  # IP
                        self.ui.tableWidget.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(row[3])))  # Port
                        self.ui.tableWidget.setItem(row_index, 3, QtWidgets.QTableWidgetItem(row[4]))  # Login
                        self.ui.tableWidget.setItem(row_index, 4, QtWidgets.QTableWidgetItem(row[5]))  # Password
                        row_index += 1  # Номер строки
                    self.startposition()  # Стартовая позиция для ListEdit
                else:
                    self.ui.plainTextEdit_Memo.appendPlainText('Запрос пустой!')
            except Exception as e:
                self.ui.plainTextEdit_Memo.appendPlainText('Ошибка при выполнении запроса в loaddata '
                                                           'settings {error}'.format(error=e))

            try:
                # заполнение таблицы мониторинга
                cursor.execute('SELECT * FROM main')
                conn.commit()
                result = cursor.fetchall()  # Результат запроса

                if result is not None:
                    self.ui.tableWidget_Monitoring.setRowCount(len(result))  # Устанавливаем кол-во строк для вывода
                    row_index = 0
                    for row in result:
                        # Заполнение tableWidget
                        self.__list_id.append(row[0])  # Запись Id оборудование в список
                        self.ui.tableWidget_Monitoring.setItem(row_index, 0, QtWidgets.QTableWidgetItem(row[1]))  # Name
                        self.ui.tableWidget_Monitoring.setItem(row_index, 1, QtWidgets.QTableWidgetItem(row[2]))  # IP
                        self.ui.tableWidget_Monitoring.setItem(row_index, 2,
                                                               QtWidgets.QTableWidgetItem(str(row[3])))  # Port
                        self.ui.tableWidget_Monitoring.setItem(row_index, 3,
                                                               QtWidgets.QTableWidgetItem(row[4]))  # Login
                        self.ui.tableWidget_Monitoring.setItem(row_index, 4,
                                                               QtWidgets.QTableWidgetItem(row[5]))  # Password
                        self.ui.tableWidget_Monitoring.setItem(row_index, 5,
                                                               QtWidgets.QTableWidgetItem(row[6]))  # hack_rf status
                        self.ui.tableWidget_Monitoring.setItem(row_index, 6,
                                                               QtWidgets.QTableWidgetItem(row[7]))  # generate status
                        row_index += 1  # Номер строки
                else:
                    print('Запрос пустой!')
            except Exception as e:
                print('Ошибка при выполнении запроса в loaddata monitoring {error}'.format(error=e))

    def load_commands(self):
        """
            В данной функции производится загрузка команд с БД
        """
        with sqlite3.connect(self.__path_db) as conn:
            cursor = conn.cursor()
            self.__list_commands = []
            try:
                cursor.execute('SELECT command FROM command')
                conn.commit()
                result = cursor.fetchall()  # Результат запроса

                if result is not None:
                    for i_data in result:
                        self.__list_commands.append(i_data[0])
            except Exception as e:
                self.ui.plainTextEdit_Memo.appendPlainText('Ошибка при загрузке команд из БД {error}'.format(error=e))

    def save_data(self):
        """
            В данной функции происходит сохранение новых данных или изменений, которые были внесены в таблицу
        """
        name = self.ui.Name_lineEdit.text()
        ip = self.ui.Ip_lineEdit_2.text()
        port = self.ui.Port_lineEdit_3.text()
        login = self.ui.Login_lineEdit_4.text()
        password = self.ui.Passw_lineEdit_5.text()

        with sqlite3.connect(self.__path_db) as conn:
            cursor = conn.cursor()

            try:
                int_port = int(port)  # Проверка Порт является числом или нет
                is_ipadress(ip)  # Проверка это Ip Адрес
            except Exception as e:
                self.ui.plainTextEdit_Memo.appendPlainText('Port не является числом! или '
                                                           'IP адрес не корректен! {error}'.format(error=e))
            else:
                if self.__cur_data['id'] != 0:
                    try:
                        cursor.execute("UPDATE main SET name=?, ip=?, port=?, login=?, "
                                       "password=? WHERE id=?", (name, ip, port, login, password, self.__cur_data['id']))
                        conn.commit()
                    except Exception as e:
                        self.ui.plainTextEdit_Memo.appendPlainText('Ошибка обновления данных {error}'.format(error=e))

                else:
                    try:
                        cursor.execute("INSERT INTO main (name, ip, port, login, password) VALUES (?, ?, ?, ?, ?)",
                                       (name, ip, port, login, password))
                        conn.commit()
                    except Exception as e:
                        self.ui.plainTextEdit_Memo.appendPlainText('Ошибка записи данных в БД {error}'.format(error=e))

            finally:
                self.load_data_sql()  # Обновление таблицы

    def add_data(self):
        """
            Запись данных в LineEdit при нажатии на кнопку Добавить
        """
        self.__cur_data['id'] = 0
        self.ui.Name_lineEdit.setText('Адрес объекта')  # Столбец Name
        self.ui.Ip_lineEdit_2.setText('IP Адрес')  # Столбец IP
        self.ui.Port_lineEdit_3.setText('Порт')  # Столбец Port
        self.ui.Login_lineEdit_4.setText('Login')  # Столбец Login
        self.ui.Passw_lineEdit_5.setText('Password')  # Столбец Password

    def delete_data(self):
        """
            Функция для удаления данных из БД. Затем происходит обновление таблицы
        """
        with sqlite3.connect(self.__path_db) as conn:
            cursor = conn.cursor()
            if self.__cur_data['id'] != 0:
                try:
                    cursor.execute("DELETE FROM main WHERE id=?", (self.__cur_data['id'],))
                    conn.commit()
                except Exception as e:
                    self.ui.plainTextEdit_Memo.appendPlainText("Ошибка в при удалении данных из таблицы"
                                                               " {error}".format(error=e))
                else:
                    self.load_data_sql()  # Обновление таблицы
                    self.startposition()  # Установление стартового положения для LineEdit
            else:
                self.ui.plainTextEdit_Memo.appendPlainText('Не выбрана строка для удаления')

    # Settings__________________________________________________________________________________________________________

    # Monitoring________________________________________________________________________________________________________
    def one_monitclick(self):
        """
            Реакция на одинарный клик. Подставляем значения name и ip из таблицы в Label_cur_dev
        """
        for item in self.ui.tableWidget_Monitoring.selectedItems():
            try:
                self.__cur_data['name'] = (self.ui.tableWidget_Monitoring.item
                                           (item.row(), 0).text())  # Запись текущего имени
                self.__cur_data['id'] = self.__list_id[item.row()]  # Запись текущего ID
                self.__cur_data['ip'] = self.ui.tableWidget_Monitoring.item(item.row(), 1).text()   # Запись текущего IP
                self.__cur_data['port'] = int(self.ui.tableWidget_Monitoring.item(
                    item.row(), 2).text())    # Запись текущего Порта
                self.__cur_data['login'] = self.ui.tableWidget_Monitoring.item(
                    item.row(), 3).text()    # Запись текущего логина
                self.__cur_data['passw'] = self.ui.tableWidget_Monitoring.item(
                    item.row(), 4).text()    # Запись текущего пароля

                self.ui.label_cur_dev.setText('Текущее устройство: ' + ''.join(
                    [self.ui.tableWidget_Monitoring.item(item.row(), 0).text(), ' ',
                     self.ui.tableWidget_Monitoring.item(item.row(), 1).text()]))
            except Exception as e:
                self.ui.plainTextEdit_Memo.appendPlainText('Ошибка записи данных в '
                                                           'Label_cur_dev {error}'.format(error=e))

    def start_hackrf(self):
        start_stop = ''
        if self.__status_button['hack_rf'] == 1:
            start_stop = 'stop '
            self.__status_button['hack_rf'] = 0
            self.ui.transl_but.setText('Старт Трансляции')
            self.ui.plainTextEdit_Memo.appendPlainText('Остановка Трансляции ' + str(datetime.datetime.now()))

        elif self.__status_button['hack_rf'] == 0:
            start_stop = 'start '
            self.__status_button['hack_rf'] = 1
            self.ui.transl_but.setText('Стоп Трансляции')
            self.ui.plainTextEdit_Memo.appendPlainText('Старт Трансляции ' + str(datetime.datetime.now()))

        new_connect = connect_ssh.SSHConnectingAndExec(hostname=self.__cur_data['ip'], port=self.__cur_data['port'],
                                                       username=self.__cur_data['login'],
                                                       password=self.__cur_data['passw'],
                                                       command=start_stop + self.__list_commands[0])

        result = new_connect.start_connection()
        self.ui.plainTextEdit_Memo.appendPlainText(self.__cur_data['name'] + ' ' + self.__cur_data['ip'] + '\n' + result)

    def start_generate(self):
        start_stop = ''
        if self.__status_button['generation'] == 1:
            start_stop = 'stop '
            self.__status_button['generation'] = 0
            self.ui.generator_but.setText('Старт Генерации')
            self.ui.plainTextEdit_Memo.appendPlainText('Остановка Генерации ' + str(datetime.datetime.now()))

        elif self.__status_button['generation'] == 0:
            start_stop = 'start '
            self.__status_button['generation'] = 1
            self.ui.generator_but.setText('Стоп Генерации')
            self.ui.plainTextEdit_Memo.appendPlainText('Старт Генерации ' + str(datetime.datetime.now()))

        new_connect = connect_ssh.SSHConnectingAndExec(hostname=self.__cur_data['ip'], port=self.__cur_data['port'],
                                                       username=self.__cur_data['login'],
                                                       password=self.__cur_data['passw'],
                                                       command=start_stop + self.__list_commands[1])
        result = new_connect.start_connection()
        self.ui.plainTextEdit_Memo.appendPlainText(
            self.__cur_data['name'] + ' ' + self.__cur_data['ip'] + '\n' + result)

    def status_serv(self):
        status = 'systemctl status '
        self.ui.plainTextEdit_Memo.appendPlainText('Вывод статуса оборудования ' + str(datetime.datetime.now()) + '\n')
        try:
            new_connect = connect_ssh.SSHConnectingAndExec(hostname=self.__cur_data['ip'], port=self.__cur_data['port'],
                                                           username=self.__cur_data['login'],
                                                           password=self.__cur_data['passw'],
                                                           command=status + self.__list_commands[2],
                                                           command2=status + self.__list_commands[3]
                                                           )
            result = new_connect.start_connection()  # Получение результата функции

            self.ui.plainTextEdit_Memo.appendPlainText(self.__cur_data['name'] + ' ' + self.__cur_data['ip'])
            self.ui.plainTextEdit_Memo.appendPlainText('Статус Трансляции')
            self.ui.plainTextEdit_Memo.appendPlainText(result)
            self.ui.plainTextEdit_Memo.insertPlainText('Статус Генерации')
        except Exception as e:
            self.ui.plainTextEdit_Memo.appendPlainText('Ошибка в выполнении shh запроса {error}'.format(error=e))

def is_ipadress(ip: str):
    # Регулярное выражение для проверки формата IP-адреса
    ip_regex = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'

    # Проверка соответствия формату IP-адреса
    if re.match(ip_regex, ip):
        # Проверка диапазона каждого числа в IP-адресе
        for octet in ip.split('.'):
            if not 0 <= int(octet) <= 255:
                raise ValueError
        return True
    else:
        raise ValueError


def create_app():
    app = QtWidgets.QApplication(sys.argv)
    win = window()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    create_app()
