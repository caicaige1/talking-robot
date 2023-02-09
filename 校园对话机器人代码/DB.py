import pymysql


# mysql_config = {
#     'server': 'localhost',
#     'user': 'sa',
#     'password': '812130dingyi',
#     'database': 'UserDB',
#     'charset': 'utf8',
#     'autocommit': True
#     'cursorclass': pymysql.cursors.DictCursor
# }


class Mysql:
    # 构造函数
    def __init__(self):
        # 连接数据库
        self.conn = pymysql.connect(host='localhost',
                                    user='project',
                                    password='4tiDewEMzG3tkh27',
                                    database='project',
                                    charset = 'utf8mb4',
                                    cursorclass=pymysql.cursors.DictCursor
                                    )
        self.conn.autocommit(True)
        # 创建游标对象
        self.cursor = self.conn.cursor()


    def query(self, sql):
        return self.cursor.execute(sql)

    def __del__(self):
        # 释放游标对象
        self.cursor.close()
        # 提交事物
        self.conn.commit()
        # 关闭 mysql 的连接
        self.conn.close()
