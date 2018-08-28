import sqlite3

class YchDb:
    # Queries
    __create_tables_query = (
        'CREATE TABLE IF NOT EXISTS ychs (chatid bigint,ychid int,'
        'maxprice float,endtime bigint,link varchar,'
        'PRIMARY KEY (chatid, ychid))'
    )
    __add_new_query = (
        'INSERT OR REPLACE INTO ychs (chatid,ychid,maxprice,endtime,link) '
        'VALUES (?,?,?,?,?)'
    )
    __select_all_query = 'SELECT * FROM ychs'
    __select_all_by_user_query = 'SELECT (ychid) FROM ychs WHERE chatid=?'
    __delete_query = 'DELETE FROM ychs WHERE ychid = ?'

    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path,check_same_thread=False)
        self.__init_db()

    def __init_db(self):
        cursor = self.conn.cursor()
        cursor.execute(self.__create_tables_query)
        self.conn.commit()

    def add_new_ych(self, ychdata):
        cursor = self.conn.cursor()
        cursor.execute(self.__add_new_query, ychdata)
        self.conn.commit()   

    def get_all_watches(self):
        cursor = self.conn.cursor()
        cursor.execute(self.__select_all_query)
        return cursor.fetchall()

    def get_all_user_watches(self, userid):
        cursor = self.conn.cursor()
        cursor.execute(self.__select_all_by_user_query, (userid,))
        return cursor.fetchall()

    def delete_watch(self, watchid):
        cursor = self.conn.cursor()
        cursor.execute(self.__delete_query, (watchid,))
        self.conn.commit()    