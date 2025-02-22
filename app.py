from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_paginate import Pagination, get_page_parameter
import sqlite3, json
import numpy as np
from datetime import timedelta
from . import AnalyzeMorpheme, record_utils, database_utils, sort_utils, stats_utils
import time, os

# 開発環境内では
# flask --app app --debug run で起動
app = Flask(__name__, template_folder='templates')
# セッションを安全に管理するためのキー

app.permanent_session_lifetime = timedelta(minutes=30)
# SQLAlchemyをセッション管理専用に設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///session.db'  # セッション用のデータベース
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = SQLAlchemy(app)
app.config['SESSION_PERMANENT'] = False

# データベースとセッションの初期化
db = app.config['SESSION_SQLALCHEMY']
Session(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(10), unique=True)
    password = db.Column(db.String(18))

@app.before_request
def create_session_table():
    db.create_all()  # セッションテーブルを作成

###################################################
##################  管理者ページ  ##################
###################################################
"""
        CREATE TABLE IF NOT EXISTS upper10 (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        original_text   TEXT NOT NULL,
        furigana_text   TEXT NOT NULL,
        length          INTEGER NOT NULL,
        head            TEXT NOT NULL,
        tail            TEXT NOT NULL,
        created_at      DATETIME DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+9 hours'))
        )
"""
# ユーザー登録用のルート
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
        
#         # パスワードをハッシュ化
#         hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
#         # 新しいユーザーを作成
#         new_user = User(username=username, password=hashed_password)
        
#         try:
#             # データベースにユーザーを追加
#             db.session.add(new_user)
#             db.session.commit()
#             flash('User successfully registered!')
#             return redirect(url_for('login'))
#         except:
#             flash('Username already exists.')
#             return redirect(url_for('register'))
    
#     return render_template('register.html')

# @app.route('/delete_all')
# def delete_all():
#     conn = sqlite3.connect('database.db')
#     cur = conn.cursor()
    
#     # レコードを削除するSQLクエリ
#     cur.execute('DELETE FROM upper10')
#     # 変更をコミット
#     conn.commit()
#     # データベース接続を閉じる
#     conn.close()
#     return render_template('index.html')

# ユーザーローダー関数（Flask-Login用）
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("in")
        username = request.form['username']
        password = request.form['password']
        print(username, password)
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            session['user_id'] = user.id  # セッションにユーザーIDを保存
            return redirect(url_for('admin'))
        else:
            return 'Invalid username or password'
    
    return render_template('login.html')

# ログアウト
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()  # セッションをクリア
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin():
    # login機能
    return render_template('admin.html')

@app.route('/modify', methods = ['POST'])
def modify():
    return render_template('modify.html', code=0)

@app.route('/search_record', methods = ['POST'])
def search_record():
    id = request.form.get('word_id')
    if id == '':
        return "ID入れてね<br><button type=\"button\" onclick=\"history.back()\">戻る</button>"
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    sql = "SELECT * FROM upper10 where id = " + str(id)
    cur.execute(sql)
    record = cur.fetchall()
    conn.close()
    if record == []:
        return "ないよ～<br><button type=\"button\" onclick=\"history.back()\">戻る</button>"
    return render_template('modify.html', code=1, record=record[0])

@app.route('/execute_update', methods = ['POST'])
def execute_update():
    updated_record = []
    for i in range(6):
        if request.form.get(f'new-{i}') != '':
            updated_record.append(request.form.get(f'new-{i}'))
        else:
            updated_record.append(request.form.get(f'old-{i}'))
    database_utils.update_record(updated_record)
    # return updated_record
    return "更新が完了しました．<br><a href=\"/\">トップページに戻る</a>"
@app.route('/execute_delete', methods = ['POST'])
def execute_delete():
    id = request.form.get('word_id')
    database_utils.delete_record_by_id(id)
    return "削除が完了しました．<br><a href=\"/\">トップページに戻る</a>"

@app.route('/test', methods = ['POST'])
def test():
    return "access success"


# アップロードページ
@app.route('/upload', methods=['POST'])
def upload():
    return render_template('upload.html')

# アップロード内容を表示
@app.route('/show_up_content', methods=['POST'])
def show_up_content():
    words = request.form['upper10_words']
    words_list = AnalyzeMorpheme.reshape_words(words) # \r\nで分割
    records = record_utils.make_records_v2(words_list)
    print(records)
    return render_template('status_table.html', records=records)

# アップロード内容をテーブル形式で表示
@app.route('/submit_table', methods=['POST'])
def submit_table():
    # POSTリクエストで送信されたデータを処理
    table_data = []
    print("form\n", len(request.form))
    for i in range(len(request.form) // 7):  # 各行は7つのセルを持つと仮定
        row = [
            request.form.get(f'row-{i}-0'),
            request.form.get(f'row-{i}-1'),
            request.form.get(f'row-{i}-2'),
            request.form.get(f'row-{i}-3'),
            request.form.get(f'row-{i}-4'),
            request.form.get(f'row-{i}-5'),
            request.form.get(f'row-{i}-6')
        ]
        table_data.append(row)
    for i in range(len(table_data)):
        table_data[i][5] = int(table_data[i][5])
        table_data[i][6] = int(table_data[i][6])
    table_data = record_utils.update_record(table_data)
    return render_template('updated_table.html', records=table_data)

@app.route('/final_table', methods = ['POST'])
def final_table():
    # POSTリクエストで送信されたデータを処理
    table_data = []
    for i in range(len(request.form) // 7):  # 各行は7つのセルを持つと仮定
        row = [
            request.form.get(f'row-{i}-0'),
            request.form.get(f'row-{i}-1'),
            request.form.get(f'row-{i}-2'),
            request.form.get(f'row-{i}-3'),
            request.form.get(f'row-{i}-4'),
        ]
        table_data.append(row)
    # アップデート後のデータからフリガナのみのリストを作成する
    furigana_list = [row_data[1] for row_data in table_data]
    
    # 類似度（Levenshtein距離）の高いペアのインデックスを取得
    tuple_list = record_utils.get_similar_pair(furigana_list, furigana_list)
    table_data = record_utils.concat_similar_input(table_data, tuple_list)
    return render_template('show_levenshtein_input_input.html', records=table_data)


@app.route('/compare_database', methods = ['POST'])
def compare_database():
    # POSTリクエストで送信されたデータを処理
    table_data = []
    print("after levenshtein\n", request.form)
    for i in range(len(request.form) // 7):  # 各行は7つのセルを持つと仮定
        row = [
            request.form.get(f'row-{i}-check'),
            request.form.get(f'row-{i}-id'),
            request.form.get(f'row-{i}-0'),
            request.form.get(f'row-{i}-1'),
            request.form.get(f'row-{i}-2'),
            request.form.get(f'row-{i}-3'),
            request.form.get(f'row-{i}-4'),
        ]
        table_data.append(row)
    table_data = [ row[2:] for row in table_data if row[0] == 'on' ] # チェックされたもののみフィルタリング
    sql = '''SELECT id, original_text, furigana_text, length, head, tail FROM upper10'''
    previous_records = database_utils.select_previous_record(sql)
    input_furigana_list = [row_data[1] for row_data in table_data]
    db_furigana_list = [row_data[2] for row_data in previous_records]
    tuple_list = record_utils.get_similar_pair(input_furigana_list, db_furigana_list)
    table_data = record_utils.concat_similar_record_in_db(table_data, previous_records, tuple_list)
    # for i in range(1, len(previous_records)+1):
    #     database_utils.delete_record_by_id(i)
    # database_utils.insert_record(table_data) # データをDBに登録
    # return "hello"
    return render_template('show_levenshtein_input_db.html', records=table_data)

@app.route('/regist_record', methods = ['POST'])
def regist_record():
    # POSTリクエストで送信されたデータを処理
    table_data = []
    print("after levenshtein\n", request.form)
    for i in range(len(request.form) // 7):  # 各行は7つのセルを持つと仮定
        row = [
            request.form.get(f'row-{i}-check'),
            request.form.get(f'row-{i}-id'),
            request.form.get(f'row-{i}-0'),
            request.form.get(f'row-{i}-1'),
            request.form.get(f'row-{i}-2'),
            request.form.get(f'row-{i}-3'),
            request.form.get(f'row-{i}-4'),
        ]
        table_data.append(row)
    table_data = [ row[2:] for row in table_data if row[0] == 'on' ] # チェックされたもののみフィルタリング
    database_utils.insert_record(table_data) # データをDBに登録
    return render_template('finish_registration.html')

@app.route('/show_request', methods = ['POST'])
def show_request():
    mode = request.form.get("mode", "view")  # デフォルトは確認モード
    # 入力CSVファイルと更新後の出力CSVファイル
    input_csv = "WordPool.csv"
    output_csv = "WordPool.csv"

    # 結果を格納するリスト
    request_data = []
    print(mode, mode=="confirm")
    # CSVファイルを開く
    with open(input_csv, mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)  # 読み込んだデータをリストに変換
    # データの処理
    for row in rows:
        if row["status"] == "0":  # statusが0のデータを処理
            request_data.append((row["単語"], row["フリガナ"]))  # (単語, フリガナ) のタプルを追加
            if mode == "confirm":
                row["status"] = "1"  # statusを1に更新
                
    # 更新後のデータをCSVに書き戻し
    with open(output_csv, mode="w", encoding="utf-8", newline="") as file:
        fieldnames = ["項番", "単語", "フリガナ", "clientIP", "IPLIST", "status"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)  # 更新済みデータを書き込み
    # 結果の表示
    print(request_data)
    return render_template('show_request.html', request_data=request_data, mode=mode)
    
    # return "！{{ request_data }}<br><a href=\"/admin\">トップページに戻る</a>"

###################################################
###################################################
###################################################

###################################################
###################  一覧ページ  ###################
###################################################
@app.route('/view_records')
def view_records():
    code = 0
    sql = '''SELECT COUNT(*) FROM upper10'''
    total = database_utils.count_data(sql)
    sql = '''SELECT * FROM upper10'''
    # record_list = database_utils.select_previous_record(sql)
    records = database_utils.select_previous_record(sql)
    session['records'] = records
    # ページ番号を取得
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 100  # 1ページあたりのレコード数
    # ページネーションのためのスライスを計算
    total = len(records)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_records = records[start:end]
    # ページネーションオブジェクトを作成
    pagination = Pagination(page=page, total=total, per_page=per_page, 
                            record_name='records', css_framework='bootstrap5')
    return render_template('view_records.html', status_code=code, total=total, records=paginated_records , pagination=pagination)

    # return redirect(url_for('paginate'))
    # return render_template('view_records.html', status_code=code, total=total, records=records)

# @app.route('/view_records/paginate')
# def paginate():
#     records = session.get('records', [])
    
#     # ページ番号を取得
#     page = request.args.get(get_page_parameter(), type=int, default=1)
#     per_page = 100  # 1ページあたりのレコード数
#     # ページネーションのためのスライスを計算
#     total = len(records)
#     start = (page - 1) * per_page
#     end = start + per_page
#     paginated_records = records[start:end]
#     # ページネーションオブジェクトを作成
#     pagination = Pagination(page=page, total=total, per_page=per_page, 
#                             record_name='records', css_framework='bootstrap5')
#     return render_template('view_records.html', status_code=3, total=total, records=paginated_records , pagination=pagination)

@app.route('/refine_records', methods = ['GET', 'POST'])
def refine_records():
    code = 1
    if request.method == 'GET':
        records = session.get('records', [])
        
        # ページ番号を取得
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 100  # 1ページあたりのレコード数
        # ページネーションのためのスライスを計算
        total = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_records = records[start:end]
        # ページネーションオブジェクトを作成
        pagination = Pagination(page=page, total=total, per_page=per_page, 
                                record_name='records', css_framework='bootstrap5')
        return render_template('view_records.html', status_code=code, total=total, records=paginated_records , pagination=pagination)
    else:
        refine_info = []
        head_chars = request.form.getlist('head_char')
        tail_chars = request.form.getlist('tail_char')
        length_span = [request.form.get("slider-min"), request.form.get("slider-max")]
        user_input = request.form.get('user_input')
        refine_info = [head_chars, tail_chars, length_span, user_input]

        sql = database_utils.make_query(refine_info)
        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute(sql)
        refine_records = cur.fetchall()
        conn.close()

        records = [list(item[0:6]) for item in refine_records] # created_atは要らないので，ここでフィルタリング
        session.pop('records', None)
        session['records'] = records
        total = len(records)

        # ページ番号を取得
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 100  # 1ページあたりのレコード数
        # ページネーションのためのスライスを計算
        total = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_records = records[start:end]
        # ページネーションオブジェクトを作成
        pagination = Pagination(page=page, total=total, per_page=per_page, 
                                record_name='records', css_framework='bootstrap5')

        # return render_template('view_records.html', status_code=code, total=total, records=records)
    return render_template('view_records.html', status_code=code, total=total, records=paginated_records , pagination=pagination)

@app.route('/sort_records', methods = ['GET', 'POST'])
def sort_records():
    code = 2
    records = session.get('records', [])
    if request.method == 'GET':
        records = session.get('records', [])
        sort_style = session.get('sort_style', '')
        
        # ページ番号を取得
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 100  # 1ページあたりのレコード数
        # ページネーションのためのスライスを計算
        total = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_records = records[start:end]
        # ページネーションオブジェクトを作成
        pagination = Pagination(page=page, total=total, per_page=per_page, 
                                record_name='records', css_framework='bootstrap5')
        return render_template('view_records.html', status_code=code, total=total, sort_style=sort_style, records=paginated_records , pagination=pagination)
    else:
        sort_style = request.form.get('sort_style')
        session.pop('sort_style', None)
        session['sort_style'] = sort_style

        if sort_style == '登録順':
            records = sort_utils.sort_id(records, False)
        elif sort_style == '登録逆順':
            records = sort_utils.sort_id(records, True)
        elif sort_style == '辞書順':
            records = sort_utils.sort_dict(records, False)
        elif sort_style == '辞書逆順':
            records = sort_utils.sort_dict(records, True)
        elif sort_style == '長さ昇順':
            records = sort_utils.sort_len(records, False)
        else: # sort_style == '長さ降順'
            records = sort_utils.sort_len(records, True)
        total = len(records)
        session.pop('records', None)
        session['records'] = records
        # ページ番号を取得
        page = request.args.get(get_page_parameter(), type=int, default=1)
        per_page = 100  # 1ページあたりのレコード数
        # ページネーションのためのスライスを計算
        total = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_records = records[start:end]
        # ページネーションオブジェクトを作成
        pagination = Pagination(page=page, total=total, per_page=per_page, 
                                record_name='records', css_framework='bootstrap5')
        return render_template('view_records.html', status_code=code, total=total, sort_style=sort_style, records=paginated_records, pagination=pagination)
###################################################
###################################################
###################################################

###################################################
################  リクエストページ  ################
###################################################
def convert_form2list(form_data):
        # フォームデータを取得
    form_data = request.form

    # `row-` で始まるキーをフィルタし、ソートしてリストに変換
    data_dict = {}
    for key, value in form_data.items():
        if key.startswith("row-"):
            _, row, col = key.split("-")  # キーを分解 (例: "row-0-1")
            row = int(row)  # 行番号
            col = int(col)  # 列番号

            if row not in data_dict:
                data_dict[row] = [None, None]  # 初期化 (2列分)

            data_dict[row][col] = value  # 適切な位置にデータを格納

    # ソートしてリスト形式に変換
    result_list = [data_dict[row] for row in sorted(data_dict.keys())]
    return result_list

import csv
def write_data_to_csv(table_data):
    csv_filename = "WordPool.csv"
    file_exists = os.path.isfile(csv_filename)
    # ヘッダー情報
    header = ["項番", "単語", "フリガナ", "clientIP", "IPLIST", "status"]
    # CSVにデータを書き込む
    with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # ファイルが存在しない場合はヘッダーを書き込む
        if not file_exists:
            writer.writerow(header)

        # 現在の行数を取得（既存データの項番を考慮）
        with open(csv_filename, mode="r", encoding="utf-8") as f:
            current_line_count = sum(1 for _ in f) - 1  # ヘッダー行を除く

        # データを書き込む
        for i, row in enumerate(table_data, start=current_line_count + 1):
            writer.writerow([i] + row + [0])
    return

@app.route('/submit_request', methods=['POST'])
def submit_request():
    # 送信元のIPアドレスを取得
    forwarded_for = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip_list = forwarded_for.split(",") if forwarded_for else []
    client_ip = ip_list[0].strip() if ip_list else request.remote_addr
    
    form_data = convert_form2list(request.form)
    table_data = []
    for i, row in enumerate(form_data):
        row = row + [client_ip] + [ip_list]
        table_data.append(row)
    write_data_to_csv(table_data)
    return render_template("finish_request.html")


@app.route('/write_request', methods=['GET', 'POST'])
def write_request():
    code = 1
    
    # フォームから送られてきたテーブルデータを受け取る
    table_data = request.form.get('tableData')
    # JSON文字列をリストに変換
    if table_data:
        table_data = json.loads(table_data)

    # フリガナだけのリストを作成
    input_list_original = []
    input_furigana_list = []
    for i in range(len(table_data)):
        input_list_original.append(table_data[i][0])
        input_furigana_list.append(table_data[i][1])


    sql = '''SELECT id, original_text, furigana_text, length, head, tail FROM upper10'''
    previous_records = database_utils.select_previous_record(sql)
    db_furigana_list = [row_data[2] for row_data in previous_records]
    tuple_list = record_utils.get_similar_pair(input_furigana_list, db_furigana_list)

    suspicious_data = []
    for i in range(len(tuple_list)):
        suspicious_data.append([input_list_original[tuple_list[i][0]], previous_records[tuple_list[i][1]][0], previous_records[tuple_list[i][1]][1]])

    return render_template('send_request.html', code=code, input_data=table_data, suspicious_data=suspicious_data)
    # table_data = record_utils.concat_similar_record_in_db(table_data, previous_records, tuple_list)

    # 返答を返す（ここでは成功メッセージ）
    # return "テーブルデータを受け取りました！<br><a href=\"/request\">トップページに戻る</a>"

@app.route('/request', methods=['GET', 'POST'])
def send_request():
    if request.method == 'GET':
        code = 0
        return render_template('send_request.html', code=code)
    else:
        table_data = request.form.get('tableData')
        print(table_data)
        return "success"

###################################################
###################################################
###################################################

###################################################
###################  統計ページ  ###################
###################################################


@app.route("/data")
def data():
    return jsonify(stats_utils.make_cumulative_data())

# @app.route('/view_stats')
# def view_stats():
#     return render_template('sample.html')

@app.route('/view_stats')
def view_stats():
    sql = '''SELECT COUNT(*) FROM upper10'''
    total = database_utils.count_data(sql)

    aiu_distr_head, aiu_distr_tail = stats_utils.get_distribution()
    scaled_distr_head = stats_utils.normalize_distribution(aiu_distr_head)
    scaled_distr_tail = stats_utils.normalize_distribution(aiu_distr_tail)

    return render_template('view_stats.html', total=total, 
                           head_color=scaled_distr_head, head_num=aiu_distr_head,
                           tail_color=scaled_distr_tail, tail_num=aiu_distr_tail)
###################################################
###################################################
###################################################

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/manual')
def manual():
    return render_template('manual.html')

if __name__ == '__main__':
    app.run(debug=True)
