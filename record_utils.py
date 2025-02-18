import pandas as pd
import numpy as np
from rapidfuzz.process import cdist
from . import AnalyzeMorpheme

def make_records(word_list):
    record_list = []
    for original_word in word_list:
        tmp_list = []
        tmp_word = AnalyzeMorpheme.remove_unvoiced_chars(original_word)
        tmp_furigana = AnalyzeMorpheme.get_furigana(tmp_word)
        tmp_furigana = AnalyzeMorpheme.remove_newline_code(tmp_furigana, '\n')
        tmp_len = len(tmp_furigana)
        tmp_head = tmp_furigana[0]
        tmp_tail = AnalyzeMorpheme.get_tail_char(tmp_furigana)
        tmp_status = AnalyzeMorpheme.get_status(tmp_word, tmp_furigana, tmp_len)
        record_list.append({
            "word":       original_word,
            "furigana":   tmp_furigana,
            "length":     tmp_len,
            "head":       tmp_head,
            "tail":       tmp_tail,
            "old_status": 0,
            "status":     tmp_status
            })
    return record_list

def make_records_v2(word_list):
    record_list = []
    for original_word in word_list:
        tmp_list = []
        tmp_word = AnalyzeMorpheme.remove_unvoiced_chars(original_word)
        tmp_furigana = AnalyzeMorpheme.get_furigana(tmp_word)
        tmp_furigana = AnalyzeMorpheme.remove_newline_code(tmp_furigana, '\n')
        tmp_len = len(tmp_furigana)
        tmp_head = tmp_furigana[0]
        tmp_tail = AnalyzeMorpheme.get_tail_char(tmp_furigana)
        tmp_status = AnalyzeMorpheme.get_status(tmp_word, tmp_furigana, tmp_len)
        record_list.append([original_word,
                            tmp_furigana,
                            tmp_len,
                            tmp_head,
                            tmp_tail,
                            0,
                            tmp_status
            ])
    return record_list

def update_record(records):
    new_records = []
    for record in records:
        print(record[1], len(record[1]))
        tmp_record = []
        tmp_record.append(record[0])
        tmp_record.append(record[1])
        tmp_record.append(len(record[1]))
        tmp_record.append(record[1][0])
        tmp_record.append(AnalyzeMorpheme.get_tail_char(record[1]))
        old_status = record[6]
        tmp_record.append(old_status)
        tmp_status = AnalyzeMorpheme.get_status(record[0], record[1], len(record[1]))
        if (old_status == 1) or (old_status == 2 and tmp_status == 2):
            tmp_record.append(1)
        elif (old_status < 0) and (tmp_status == 1 or tmp_status == 2):
            tmp_record.append(2)
        else:
            continue

        new_records.append(tmp_record)
        print(new_records)
    return new_records

# def update_record(json_list):
#     record_list = []
#     for json in json_list:
#         if (json["old_status"] == "999" and json["status"] == "0") or (json["old_status"] == "1" and json["status"] == "1"):
#             json["status"] = 0
#         record_list.append(json)
    
#     return record_list

# https://rapidfuzz.github.io/RapidFuzz/Usage/process.html#cdist


# 同じリスト同士で比較する場合に類似ペアのインデックスを取得
# 入力チェックでの重複入力の検知に使用する
# [[100.   0.  75.   0.]  <-のような配列の上三角部分（対角要素を含まない）についてのみ走査
#  [  0. 100.   0. 100.]    対角要素は同一文字列なのでスコアが100
#  [  0.  75. 100.   0.]    計算量がn^2から(n^2)/2以下に低下
#  [  0. 100.   0. 100.]]
def get_indices_same_lists(score: np.ndarray):
    tuple_list = [(i, j, score[i, j]) for i in range(score.shape[0]) for j in range(i+1, score.shape[1]) if score[i, j] != 0]
    """ 以下と等価
    tuple_list = []
    for i in range(score.shape[0]):
        for j in range(i+1, score.shape[1]):
            if score[i,j] != 0:
                tuple_list.append((i, j, score[i, j]))
    """
    print(tuple_list)
    return tuple_list

# 異なるリスト同士で比較する場合に類似ペアのインデックスを取得
# 入力データとDBに登録されているデータの重複登録の検知に使用する
def get_indices_other_lists(score: np.ndarray):
    # 0でない値のインデックスを取得
    # 非ゼロ要素のインデックスと値を取得
    non_zero_indices = np.nonzero(score)
    non_zero_values = score[non_zero_indices]

    # タプルリストを作成
    tuple_list = list(zip(non_zero_indices[0], non_zero_indices[1], non_zero_values))
    return tuple_list

# ふたつのリストの全要素に関してLevenshtein距離から類似度（0-100）を測定
def calculate_similarity(queries, choices):
    # score_cutoffで指定した類似度以下はすべて0とする
    score = cdist(queries, choices, score_cutoff=80.)
    return score

def get_similar_pair(queries, choices):
    score = calculate_similarity(queries, choices)
    if queries == choices:
        tuple_list = get_indices_same_lists(score)
    else:
        tuple_list = get_indices_other_lists(score)
    return tuple_list

def make_similar_pairs(list1, list2, tuple_list):
    pair_list = []
    for t in tuple_list:
        # タプルの中の要素にインデックスでアクセス
        row, col = t[0], t[1]
        pair_list.append([list1[row], list2[col]])
    return pair_list

def concat_similar_input(main_list, cat_data):
    new_data = []
    for i, row in enumerate(main_list):
        tmp_row = []
        for tpl in cat_data:
            if i == tpl[0]:
                tmp_row = [tpl[1], main_list[tpl[1]][0], main_list[tpl[1]][1], main_list[tpl[1]][2], round(float(tpl[2]), 4)]
                row.append(tmp_row)
        new_data.append(row)
    return new_data

def concat_similar_record_in_db(table_data, db_records, cat_data):
    new_data = []
    for i, row in enumerate(table_data):
        tmp_row = []
        for tpl in cat_data:
            if i == tpl[0]:
                tmp_row = db_records[tpl[1]][0:4] + [round(float(tpl[2]), 4)]
                row.append(tmp_row)
        new_data.append(row)
    return new_data

# https://qiita.com/fujine/items/b7189c4a55da33f821e3