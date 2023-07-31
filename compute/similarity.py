
import logging


from variable.events import pause_event, stop_event, group_index
logging.basicConfig(filename='app.log', filemode='w', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG, encoding='utf-8')

import pandas as pd
import jieba
import math

# 设置日志级别
jieba.setLogLevel(jieba.logging.INFO)
calculation_status = 0
class XsdCalculator:
    def __init__(self, s1_path,s2_path):
        self.s1_path = s1_path
        self.s2_path = s2_path

    def read_data(self, col1, col2):
        # 读取 excel 表列数据
        s1 = pd.read_excel(self.s1_path, header=None, dtype=object)
        s2 = pd.read_excel(self.s2_path, header=None, dtype=object)
        # 读取 excel 指定列
        self.ss1 = s1.iloc[:, int(col1)].values
        self.ss2 = s2.iloc[:, int(col2)].values
        # 判断第一行是否为列名，如果是，则跳过第一行
        if isinstance(s1.iloc[0, int(col1)], str):
            self.ss1 = s1.iloc[1:, int(col1)].values
        else:
            self.ss1 = s1.iloc[:, int(col1)].values
        if isinstance(s2.iloc[0, int(col2)], str):
            self.ss2 = s2.iloc[1:, int(col2)].values
        else:
            self.ss2 = s2.iloc[:, int(col2)].values

    def compute_xsd(self, s1, s2):
        # 利用jieba分词与停用词表，将词分好并保存到向量中
        stopwords = []
        # 去除停用词(stopwords)和空字符
        s1_cut = [word for word in jieba.cut(s1) if (word not in stopwords) and word.strip() != '' and word.isalnum()]
        s2_cut = [word for word in jieba.cut(str(s2)) if
                  (word not in stopwords) and word.strip() != '' and word.isalnum()]  # 将ss2转换为字符串类型
        word_set = set(s1_cut).union(set(s2_cut))
        # 用字典保存两篇文章中出现的所有词并编上号
        # onehot编码处理
        word_dict = dict()
        i = 0
        for word in word_set:
            word_dict[word] = i
            i += 1
        # 根据词袋模型统计词在每篇文档中出现的次数，形成向量
        s1_cut_code = [0] * len(word_dict)
        for word in s1_cut:
            s1_cut_code[word_dict[word]] += 1
        s2_cut_code = [0] * len(word_dict)
        for word in s2_cut:
            s2_cut_code[word_dict[word]] += 1
        # 计算余弦相似度
        sum = 0
        sq1 = 0
        sq2 = 0
        for i in range(len(s1_cut_code)):
            sum += s1_cut_code[i] * s2_cut_code[i]
            sq1 += pow(s1_cut_code[i], 2)
            sq2 += pow(s2_cut_code[i], 2)
        try:
            result = round(float(sum) / (math.sqrt(sq1) * math.sqrt(sq2)), 3)
        except ZeroDivisionError:
            result = 0.0
        return result

    def calculate_similarity(self, group_size, pause_event):
        # 跟踪计算了多少个分组
        global group_count
        try:
            # 定义一个空的DataFrame，用于存储计算结果
            result_df = pd.DataFrame(columns=['ss1', 'ss2', 'similarity', '匹配结果1', '匹配结果2', '匹配结果3'])
            # 将 ss1 列表分成多个子列表
            ss1_grouped = [self.ss1[i:i + group_size] for i in range(0, len(self.ss1), group_size)]
            # 遍历每个分组，对每个ss1进行匹配计算
            global group_index
            for group_idx, ss1_group in enumerate(ss1_grouped[group_index:]):
                group_count = group_idx + 1  # 更新 group_count 变量的值
                # 检查暂停状态
                if pause_event.is_set():
                    pause_event.wait()  # 等待事件被清除，即等待恢复计算
                # 检查停止状态
                if stop_event.is_set():
                    break
                # 遍历ss1_group中的每个元素，计算与ss2中的相似度，并将匹配结果存入子DataFrame sub_df 中
                sub_df = pd.DataFrame(columns=['ss1', 'ss2', 'similarity', '匹配结果1', '匹配结果2', '匹配结果3'])
                for ss1_item in ss1_group:
                    sub_df_temp = pd.DataFrame({'ss1': [ss1_item] * len(self.ss2), 'ss2': self.ss2})
                    sub_df_temp['similarity'] = sub_df_temp.apply(lambda x: self.compute_xsd(str(x['ss1']), x['ss2']),
                                                                  axis=1)
                    sub_df_temp = sub_df_temp.sort_values(by=['similarity'], ascending=False)
                    sub_df_temp = sub_df_temp.reset_index(drop=True)
                    # 判断相似度值是否大于0
                    if sub_df_temp['similarity'].max() > 0:
                        sub_df_temp = sub_df_temp.groupby('ss1').head(3)  # 取每个ss1的前三个匹配结果
                    else:
                        sub_df_temp = pd.DataFrame(
                            columns=['ss1', 'ss2', 'similarity', '匹配结果1', '匹配结果2', '匹配结果3'])
                    sub_df_temp = sub_df_temp.drop_duplicates(subset=['ss1', 'ss2'])
                    # 如果 sub_df_temp 中的数据不足 3 条，就在 sub_df_temp 中补充空白数据
                    if len(sub_df_temp) < 3:
                        blank_df = pd.DataFrame(
                            {'ss1': [ss1_item] * (3 - len(sub_df_temp)), 'ss2': [''] * (3 - len(sub_df_temp)),
                             'similarity': [0.0] * (3 - len(sub_df_temp))})
                        sub_df_temp = pd.concat([sub_df_temp, blank_df], ignore_index=True)
                    # 对匹配结果进行排序，并存入到匹配结果1、匹配结果2、匹配结果3中
                    sub_df_temp = sub_df_temp.sort_values(by=['similarity'], ascending=False)
                    sub_df_temp.loc[sub_df_temp.index[0], '匹配结果1'] = sub_df_temp.loc[sub_df_temp.index[0], 'ss2']
                    sub_df_temp.loc[sub_df_temp.index[0], '匹配结果2'] = sub_df_temp.loc[sub_df_temp.index[1], 'ss2']
                    sub_df_temp.loc[sub_df_temp.index[0], '匹配结果3'] = sub_df_temp.loc[sub_df_temp.index[2], 'ss2']
                    # 增加三个结果的具体计算值
                    sub_df_temp.loc[sub_df_temp.index[0], '相似度1'] = sub_df_temp.loc[sub_df_temp.index[0], 'similarity']
                    sub_df_temp.loc[sub_df_temp.index[0], '相似度2'] = sub_df_temp.loc[sub_df_temp.index[1], 'similarity']
                    sub_df_temp.loc[sub_df_temp.index[0], '相似度3'] = sub_df_temp.loc[sub_df_temp.index[2], 'similarity']
                    # 删除三个匹配结果值中行索引为1和2的数据3
                    sub_df_temp = sub_df_temp.drop(index=[1, 2])
                    sub_df = pd.concat([sub_df, sub_df_temp])
                # 将当前分组的计算结果存入result_df中
                result_df = pd.concat([result_df, sub_df])
                group_index = group_idx + group_index
                if pause_event.is_set():
                    return group_index, result_df



            # 将计算结果保存到 excel 文件中
            s1 = pd.read_excel(self.s1_path, header=None, dtype=object)
            final_result = pd.concat([s1.iloc[1:].reset_index(drop=True), result_df[['匹配结果1', '相似度1',
            '匹配结果2', '相似度2', '匹配结果3', '相似度3']].reset_index(drop=True)], axis=1)
            new_columns = s1.iloc[0].tolist() + ['匹配结果1', '相似度1', '匹配结果2', '相似度2', '匹配结果3', '相似度3']
            final_result = final_result.set_axis(new_columns, axis=1, copy=False)
            # 生成结果表
            final_result.to_excel('结果汇总表.xlsx', index=False)
            self.final_result = final_result
            return group_index, result_df

        except Exception as e:
            # 捕获异常并将其记录到日志文件中
            logging.error(f'发生错误: {e}')
            raise e

    def save_result(self, file_path):
        # 将计算结果保存到 excel 文件中
        if self.final_result is not None:
            self.final_result.to_excel(file_path, index=False)





