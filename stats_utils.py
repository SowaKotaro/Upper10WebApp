from . import database_utils
import numpy as np
import sqlite3

AIUEO_LIST = ['ア', 'イ', 'ウ', 'エ', 'オ',
              'ヴ',
              'カ', 'キ', 'ク', 'ケ', 'コ',
              'ガ', 'ギ', 'グ', 'ゲ', 'ゴ',
              'サ', 'シ', 'ス', 'セ', 'ソ',
              'ザ', 'ジ', 'ズ', 'ゼ', 'ゾ',
              'タ', 'チ', 'ツ', 'テ', 'ト',
              'ダ', 'ヂ', 'ヅ', 'デ', 'ド',
              'ナ', 'ニ', 'ヌ', 'ネ', 'ノ',
              'ハ', 'ヒ', 'フ', 'ヘ', 'ホ',
              'バ', 'ビ', 'ブ', 'ベ', 'ボ',
              'パ', 'ピ', 'プ', 'ペ', 'ポ',
              'マ', 'ミ', 'ム', 'メ', 'モ',
              'ヤ', 'ユ', 'ヨ',
              'ラ', 'リ', 'ル', 'レ', 'ロ',
              'ワ', 'ヰ', 'ヱ', 'ヲ', 'ン']

def get_distribution():
    aiu_distr_head = []
    aiu_distr_tail = []
    for ja_char in AIUEO_LIST:
        sql_head = f'''SELECT COUNT(*) FROM upper10 WHERE head = \'{ja_char}\''''
        count_head = database_utils.count_data(sql_head)
        aiu_distr_head.append(count_head)

        sql_tail = f'''SELECT COUNT(*) FROM upper10 WHERE tail = \'{ja_char}\''''
        count_tail = database_utils.count_data(sql_tail)
        aiu_distr_tail.append(count_tail)
    return aiu_distr_head, aiu_distr_tail

def normalize_distribution(distr):
    min_val = np.min(distr)
    max_val = np.max(distr)
    scaled_distr = []
    scale_size = 50
    for value in distr:
        # 逆転スケーリング
        reversed_value = max_val - value

        # 正規化（0から1の範囲にスケーリング）
        normalized_value = (reversed_value) / (max_val - min_val)

        # 60から100の範囲にスケーリング
        scaled_value = scale_size + (normalized_value * (100 - scale_size))
        scaled_distr.append(scaled_value)
    return scaled_distr

# SQLite から日時ごとのデータ総数を取得
def make_cumulative_data():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DATE(created_at), COUNT(*) 
        FROM upper10 
        GROUP BY DATE(created_at) 
        ORDER BY DATE(created_at)
    """)
    data = cursor.fetchall()
    conn.close()
    print(data)
    cumulative_count = 0
    cumulative_data = []
    
    for row in data:
        cumulative_count += row[1]
        cumulative_data.append({"timestamp": row[0], "total_count": cumulative_count})    
    print(cumulative_data)
    return cumulative_data