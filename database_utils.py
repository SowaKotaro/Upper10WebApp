import sqlite3
from . import AnalyzeMorpheme

# データベースに登録
def insert_record(table_data):
    sql = '''INSERT INTO upper10 (original_text, furigana_text, length, head, tail)
         VALUES (?, ?, ?, ?, ?)'''
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.executemany(sql, table_data)
    conn.commit()
    conn.close()
    return

def update_record(upd_rec):
    print(upd_rec)
    sql = """UPDATE upper10
             SET original_text = ?, 
                 furigana_text = ?, 
                 length = ?, 
                 head = ?, 
                 tail = ?
             WHERE id = ?           """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(sql, (upd_rec[1], upd_rec[2], upd_rec[3], upd_rec[4], upd_rec[5], upd_rec[0]))
    conn.commit()
    conn.close()
    return


def count_data(sql):
    # データベースに接続
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # テーブル内に存在するデータの総数をカウント
    cur.execute(sql)

    total = cur.fetchone()[0]

    # データベース接続を閉じる
    conn.close()
    return total

def get_longest_record():
    sql = """SELECT * FROM upper10 WHERE length = (SELECT MAX(length) FROM upper10)"""
    # データベースに接続
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # テーブル内に存在するデータの総数をカウント
    cur.execute(sql)

    longest_record = cur.fetchone()
    # データベース接続を閉じる
    conn.close()
    return longest_record

def get_total_length():
    sql = """SELECT SUM(length) AS total_sum FROM upper10"""
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute(sql)
    total_length = cur.fetchone()
    total_length = total_length[0]
    conn.close()
    return total_length

def select_previous_record(sql):
    # データベースに接続
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # テーブル内のすべてのデータを取得
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    # リスト形式でデータを出力
    data_list = [list(row) for row in rows]
    return data_list

def delete_record_by_id(record_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    
    # レコードを削除するSQLクエリ
    cur.execute('DELETE FROM upper10 WHERE id = ?', (record_id,))
    
    # 変更をコミット
    conn.commit()
    # データベース接続を閉じる
    conn.close()
    return 

### making query ###

def make_query_head(refine_head):
    query = ""
    for i in range(len(refine_head)):
        if i == len(refine_head) - 1:
            query = query + "head = " + "\'" + refine_head[i] + "\'"
        else:
            query = query + "head = " + "\'" + refine_head[i] + "\'" + ' or '
    return query

def make_query_tail(refine_tail):
    query = ""
    for i in range(len(refine_tail)):
        if i == len(refine_tail) - 1:
            query = query + "tail = " + "\'" + refine_tail[i] + "\'"
        else:
            query = query + "tail = " + "\'" + refine_tail[i] + "\'" + ' or '
    return query

def make_query_h_t(refine_head, refine_tail):
    query = ""
    if len(refine_head) == 0:
        return make_query_tail(refine_tail)
    elif len(refine_tail) == 0:
        return make_query_head(refine_head)
    for i, head in enumerate(refine_head):
        for j, tail in enumerate(refine_tail):
            if i == len(refine_head) - 1 and j == len(refine_tail) - 1:
                query = query + "head = " + "\'" + head + "\' and tail = " + "\'" + tail + "\'" 
            else:
                query = query + "head = " + "\'" + head + "\' and tail = " + "\'" + tail + "\'" 
                query = query + " or "
    return query


def make_query_len(refine_length):
    if refine_length[1] == '31':
        query = "length >= " + refine_length[0]
    else:
        query = "length BETWEEN " + refine_length[0] + " AND " + refine_length[1]
    return query

def make_partial_match_query(user_input):
    query = ""

    if AnalyzeMorpheme.is_katakana(user_input) == True:
        query = "furigana_text LIKE " + '\'%' + user_input + '%\''
        violation = False
    else:
        if AnalyzeMorpheme.validate_user_input(user_input) == True:
            query = "original_text LIKE " + '\'%' + user_input + '%\''
            violation = False
        else:
            query = ""
            violation = True
    if user_input == "":
        violation = False
    return query, violation

def cat_queries_v2(queries):
    query = ""
    for i, q in enumerate(queries):
        print(i,q)
        if i == 0:
            query = q
        else:
            query = query + " and " + q
        print("now query", query)
    return query

def cat_queries(head_q, tail_q, len_q, match_q):
    query = ""
    if head_q == "" and tail_q == "":
        query = len_q
    elif head_q != "" and tail_q == "":
        query = head_q + " and " + len_q
    elif head_q == "" and tail_q != "":
        query = tail_q + " and " + len_q
    else:
        query = head_q + " and " + tail_q + " and " + len_q
    return query

def make_query(refine_info): # refine_info = [[head], [tail], [min, max]]
    sql = '''SELECT * FROM upper10 WHERE '''
    print(refine_info)
    h_t_query = make_query_h_t(refine_info[0], refine_info[1])
    
    # head_query = make_query_head(refine_info[0])
    # tail_query = make_query_tail(refine_info[1])
    length_query = make_query_len(refine_info[2])
    match_query, violation = make_partial_match_query(refine_info[3])
    # sql = sql + cat_queries(head_query, tail_query, length_query, match_query)
    queries = [h_t_query, length_query, match_query]
    # queries = [head_query, tail_query, length_query, match_query]
    print(queries)
    queries = [q for q in queries if q != '']
    print(queries)
    sql = sql + cat_queries_v2(queries)
    print(sql)
    # exit()
    if violation:
        sql = """"""
    return sql