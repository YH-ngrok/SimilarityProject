import logging
import threading

import pandas as pd

calculation_status = 0
# 创建一个线程对象
calculation_thread = None
# 定义全局变量
pause_event = threading.Event()
stop_event = threading.Event()
resume_event = threading.Event()
# 定义分组暂停、继续变量
group_index = 0


# 暂停、继续根据s1来，比如点击了暂停按钮，此时程序计算到某个分组结束就暂停计算，点击继续按钮就从暂停后的那一个分组计算

# 7 .28
# bug：当点击了暂停按钮之后，再点击继续按钮，程序不会再进行计算并停止在点击暂停按钮的时候，若此时点击停止按钮，程序下载的汇总结果是暂停之前计算的数据
# 实现暂停、继续
# 1.当点击暂停按钮之后，立马暂停所有数据，当继续执行计算时需要把上次点击暂停时剩下的数据计算完成
# 2.当点击暂停按钮之后，程序正在计算分组的数据，等分组剩下的数据计算完毕再暂停，继续执行计算的时候就从上次暂停计算完毕后一个分组继续计算



# https://github.com/YH-ngrok/sim.git