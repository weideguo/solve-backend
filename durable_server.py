# -*- coding: utf-8 -*- 
# 用于持久化redis的数据到mongodb
from dura import solve_dura,MONGODB_CONFIG

if __name__ == '__main__':
    # 启动后台进程
    if MONGODB_CONFIG:
        print("MONGODB_CONFIG [ %s ], durable server now is runing ..." % str(MONGODB_CONFIG))
        solve_dura.background()
    else:
        print("MONGODB_CONFIG [ %s ], durable server now exit" % str(MONGODB_CONFIG))

