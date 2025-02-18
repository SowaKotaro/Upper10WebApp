import sqlite3

def init_db():
    # データベースに接続（なければ新規作成）
    conn = sqlite3.connect('database.db')
    # カーソルを取得
    cursor = conn.cursor()

    sql = """
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
    # テーブルの作成
    cursor.execute(sql)

    # コミットして接続を閉じる
    conn.commit()
    conn.close()

# 初期化関数を実行
init_db()
