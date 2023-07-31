import math
import tkinter as tk
import time
from datetime import datetime
from tkinter import filedialog, messagebox
import threading
import pandas as pd
import tkinter.messagebox
import os
import logging

from compute.similarity import XsdCalculator
from variable.events import pause_event, stop_event

logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG, encoding='utf-8')

# Temporary file path
TEMP_FILE = 'temp.txt'
calculation_thread = None
calculation_status = 1

global group_index
group_index = 0
#
#
# stop_event = threading.Event()
# pause_event = threading.Event()


def select_file1():
    full_path = filedialog.askopenfilename()
    file1_path.set(full_path)

def select_file2():
    full_path = filedialog.askopenfilename()
    file2_path.set(full_path)

global result_df
result_df = pd.DataFrame()
def do_calculate():
    try:
        start_time = datetime.now()
        print(f'开始读取数据, 计算开始时间: {start_time}')
        # 创建 XsdCalculator 对象
        xsd_calculator = XsdCalculator(file1_path.get(), file2_path.get())
        # 读取数据
        xsd_calculator.read_data(col1_entry.get(), col2_entry.get())
        print('数据读取完成')
        print('开始计算')
        # 声明全局变量
        global group_index, result_df
        # 接收从 calculate_similarity 方法返回的分组索引和结果数据框
        # group_index, result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)

        new_group_index, new_result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)
        group_index += new_group_index
        result_df = pd.concat([result_df, new_result_df])


        # 检查暂停事件是否被设置
        while pause_event.is_set():
            print(f'计算已暂停')
            # 等待暂停事件被清除
            pause_event.wait()
            print(f'计算已继续')
            # 继续计算
            # group_index, result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)

            new_group_index, new_result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()),
                                                                                 pause_event)
            group_index += new_group_index
            result_df = pd.concat([result_df, new_result_df])

        end_time = datetime.now()
        duration = end_time - start_time
        print(f"计算完成, 计算结束时间: {end_time}, 计算所花费时间: {duration}")
        tk.Button(root, text="下载汇总结果", command=download).grid(row=6, columnspan=3)
    except Exception as e:
        logging.error(f'发生错误: {e}')

def calculate():
    # 是否上传文件
    if not file1_path.get() or not file2_path.get():
        tk.messagebox.showerror("错误", "请选择两个Excel文件")
        return
    global calculation_thread, calculation_status
    calculation_status = 0
    with open(TEMP_FILE, 'w') as temp_file:
        temp_file.write(file1_path.get() + '\n')
        temp_file.write(file2_path.get() + '\n')
        temp_file.write(col1_entry.get() + '\n')
        temp_file.write(col2_entry.get() + '\n')
        temp_file.write(group_size_entry.get() + '\n')
    # 清除停止事件
    stop_event.clear()
    # 清除暂停事件
    pause_event.clear()
    # 创建计算线程
    calculation_thread = threading.Thread(target=do_calculate)
    # 启动计算线程
    calculation_thread.start()

def download():
    dir_path = filedialog.askdirectory()
    if dir_path:
        file_path = os.path.join(dir_path, '结果汇总表.xlsx')
        if os.path.exists(file_path):
            os.remove(file_path)
        global result_df
        s1 = pd.read_excel(file1_path.get(), header=None, dtype=object)
        final_result = pd.concat([s1.iloc[1:].reset_index(drop=True), result_df[
            ['匹配结果1', '相似度1','匹配结果2', '相似度2','匹配结果3','相似度3']].reset_index(drop=True)], axis=1)
        new_columns = s1.iloc[0].tolist() + \
                      ['匹配结果1', '相似度1', '匹配结果2', '相似度2', '匹配结果3','相似度3']

        final_result = final_result.set_axis(new_columns, axis=1, copy=False)
        final_result.to_excel(file_path, index=False)

def pause():
    pause_event.set()
    tk.messagebox.showinfo("提示", "计算已暂停!")

def resume():
    pause_event.clear()
    tk.messagebox.showinfo("提示", "计算已继续!")

def stop():
    stop_event.set()
    tk.Button(root, text="下载汇总结果", command=download).grid(row=6, columnspan=3)
    tk.messagebox.showinfo("提示", "计算已停止!")


def check_previous_calculation():
    if os.path.exists(TEMP_FILE):
        with open(TEMP_FILE, 'r') as temp_file:
            lines = temp_file.readlines()
            if len(lines) >= 5:
                file1_path_str = lines[0].strip()
                file2_path_str = lines[1].strip()
                col1_entry_str = lines[2].strip()
                col2_entry_str = lines[3].strip()
                group_size_entry_str = lines[4].strip()

                file1_path.set(file1_path_str)
                file2_path.set(file2_path_str)
                col1_entry.delete(0, tk.END)
                col1_entry.insert(0, col1_entry_str)
                col2_entry.delete(0, tk.END)
                col2_entry.insert(0, col2_entry_str)
                group_size_entry.delete(0, tk.END)
                group_size_entry.insert(0, group_size_entry_str)
                if messagebox.askyesno("提示", "是否继续上一次未完成的任务?"):
                    calculate()
                else:
                    # 在这里添加代码来清空 Entry 控件的值
                    file1_path.set('')
                    file2_path.set('')
                    col1_entry.delete(0, tk.END)
                    col2_entry.delete(0, tk.END)
                    group_size_entry.delete(0, tk.END)


# 设计图形界面
root = tk.Tk()
root.title("计算Excel文件相似度")
file1_path = tk.StringVar()
file2_path = tk.StringVar()
tk.Label(root, text="请选择Excel目标文件:").grid(row=0, column=0)
tk.Entry(root, textvariable=file1_path).grid(row=0, column=1)
tk.Button(root, text="选择文件", command=select_file1).grid(row=0, column=2)
tk.Label(root, text="请选择Excel匹配文件:").grid(row=1, column=0)
tk.Entry(root, textvariable=file2_path).grid(row=1, column=1)
tk.Button(root, text="选择文件", command=select_file2).grid(row=1, column=2)
tk.Label(root, text="请输入目标文件的指定列:").grid(row=2, column=0)
col1_entry = tk.Entry(root)
col1_entry.grid(row=2, column=1)
tk.Label(root, text="请输入匹配文件的指定列:").grid(row=3, column=0)
col2_entry = tk.Entry(root)
col2_entry.grid(row=3, column=1)
tk.Label(root, text="请输入分组数据大小:").grid(row=4, column=0)
group_size_entry = tk.Entry(root)
group_size_entry.grid(row=4, column=1)
tk.Button(root, text="计算相似度", command=calculate).grid(row=5, columnspan=3)
tk.Button(root, text="暂停", command=pause).grid(row=7, column=0)
tk.Button(root, text="继续", command=resume).grid(row=7, column=1)
tk.Button(root, text="停止", command=stop).grid(row=7, column=2)

































# def do_calculate():
#     try:
#         start_time = datetime.now()
#         print(f'开始读取数据, 计算开始时间: {start_time}')
#         # 创建 XsdCalculator 对象
#         xsd_calculator = XsdCalculator(file1_path.get(), file2_path.get())
#         # 读取数据
#         xsd_calculator.read_data(col1_entry.get(), col2_entry.get())
#         print('数据读取完成')
#         print('开始计算')
#         # 声明全局变量
#         global group_index, result_df
#         # 接收从 calculate_similarity 方法返回的分组索引和结果数据框
#         group_index, result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)
#         # 检查暂停事件是否被设置
#         while pause_event.is_set():
#             # print(f'计算已暂停，当前分组为{group_index}')
#             print(f'计算已暂停')
#             # 等待暂停事件被清除
#             pause_event.wait()
#             if not pause_event.is_set():
#                 break
#             # print(f'计算已继续，当前分组为{group_index}')
#             print(f'计算已继续')
#             # 继续计算
#             group_index, result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)
#         end_time = datetime.now()
#         duration = end_time - start_time
#         print(f"计算完成, 计算结束时间: {end_time}, 计算所花费时间: {duration}")
#         tk.Button(root, text="下载汇总结果", command=download).grid(row=6, columnspan=3)
#     except Exception as e:
#         logging.error(f'发生错误: {e}')

# def do_calculate():
#     try:
#         start_time = datetime.now()
#         print(f'开始读取数据, 计算开始时间: {start_time}')
#         # 创建 XsdCalculator 对象
#         xsd_calculator = XsdCalculator(file1_path.get(), file2_path.get())
#         # 读取数据
#         xsd_calculator.read_data(col1_entry.get(), col2_entry.get())
#         print('数据读取完成')
#         print('开始计算')
#         # 声明全局变量
#         global group_index, result_df
#         # 接收从 calculate_similarity 方法返回的分组索引和结果数据框
#         group_index, result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)
#         # 检查暂停事件是否被设置
#         while True:
#             if pause_event.is_set():
#                 # print(f'计算已暂停，当前分组为{group_index}')
#                 print(f'计算已暂停')
#                 # 等待暂停事件被清除
#                 pause_event.wait()
#                 # print(f'计算已继续，当前分组为{group_index}')
#                 print(f'计算已继续')
#             else:
#                 # 继续计算
#                 group_index, result_df = xsd_calculator.calculate_similarity(int(group_size_entry.get()), pause_event)
#                 if group_index == -1:
#                     break
#         end_time = datetime.now()
#         duration = end_time - start_time
#         print(f"计算完成, 计算结束时间: {end_time}, 计算所花费时间: {duration}")
#         print("计算完成")
#         tk.Button(root, text="下载汇总结果", command=download).grid(row=6, columnspan=3)
#     except Exception as e:
#         logging.error(f'发生错误: {e}')
