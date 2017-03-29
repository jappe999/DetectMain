import pymysql
from colorama import init, Fore, Back, Style

class Database(object):
    def __init__(self, user, password, database):
        try:
            init()
            self.db = pymysql.connect (
                        host="127.0.0.1",
                        port=3306,
                        user=user,
                        password=password,
                        db=database
                      )
            self.cursor = self.db.cursor()
        except Exception as e:
            print(Fore.RED + "Error 0x1:")
            print(e)
            print(Style.RESET_ALL)
            exit()

    def fetch(self, command):
        try:
            self.cursor.execute(command)
            response = self.cursor.fetchall()
            return response
        except Exception as e:
            print('MySQL executing error', str(e))
            return False


    def execute(self, command):
        try:
            self.cursor.execute(command)
            self.db.commit()
            return True
        except Exception as e:
            print('MySQL executing error', str(e))
            return False

    def close(self):
        self.cursor.close()
        self.db.close()
