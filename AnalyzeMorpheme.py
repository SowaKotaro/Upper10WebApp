import MeCab
import re


# クラスとして定義するかは要検討
# class TextFormatter(): 
# プログラム名もsanitize_text.pyとanalyze_text.pyとかに分割するかも


# 入力テキスト内に含まれる改行コードを削除
def remove_newline_code(word, symbol):
    return word.replace(symbol, '')

# 複数行の入力を各行ごとのリストに変換し項番号や中黒を削除
def reshape_words(words):
    print(words)
    symbol = '\r\n' # Notion,Chromeの改行文字はCRLF
    whitespace_pattern = r'[\s\u3000]'
    bullet_pattern = '^[0-9.\- ]+' # [- ],[42. ]の正規表現
    word_list = words.split(symbol) # 改行コードで分割する
    word_list = [re.sub(whitespace_pattern, '', word) for word in word_list]
    word_list = [re.sub(bullet_pattern, '', word) for word in word_list] # Bulletを削除する
    word_list = [word for word in word_list if word] # リスト内に空の要素があった場合に削除する
    print(word_list)
    return word_list

# 音声にならない文字を削除
def remove_unvoiced_chars(input_word):
    # 削除する文字
    pattern = r"[・=＝、。，．\(\)（）\[\]「」]"
    return re.sub(pattern, '', input_word)

# フリガナを取得
def get_furigana(input_word):
    # 辞書の相対パス．今回はNEologdで固有名詞にある程度対応
    mecabrc_path = "./mecab/mecabrc" # mecabrcの内容が無ければエラーになる
    dict_path = "./mecab/dic/mecab-ipadic-neologd"
    tagger_yomi = MeCab.Tagger(f"-r {mecabrc_path} -Oyomi -d {dict_path}")

    # parseで入力文字列の読み仮名を解析（カタカナ）
    furigana = tagger_yomi.parse(input_word)
    return furigana

# 末尾文字をフリガナから取得
def get_tail_char(furigana):
    small_chars = ['ァ','ィ','ゥ','ェ','ォ','ャ','ュ','ョ','ッ','ヮ']
    big_chars   = ['ア','イ','ウ','エ','オ','ヤ','ユ','ヨ','ツ','ワ']

    if furigana[-1] in small_chars: # 最後の文字が小文字なら対応した大文字を末尾文字とする
        index_of_small_char = small_chars.index(furigana[-1])
        return big_chars[index_of_small_char]
    if furigana[-1] == 'ー': # 最後の文字が長音の場合
        if furigana[-2] in small_chars: # 最後から2番目の文字が小文字なら対応した大文字を末尾文字とする
            index_of_small_char = small_chars.index(furigana[-2])
            return big_chars[index_of_small_char]
        else: # 最後から2番目の文字が大文字ならその文字を末尾文字とする
            return furigana[-2]
    return furigana[-1]

def is_katakana(furigana):
    pattern = r'^[\u30A0-\u30FFー]+$' # UTF-8でカタカナのみを表す正規表現パターン
    return bool(re.match(pattern, furigana)) # パターンにマッチするかどうかをチェック

def get_status(original, furigana, length):
    status_code = 1
    if length < 10:
        status_code = -1 # レギュレーション違反
        return status_code
    Ori_bool = is_katakana(original)
    Furi_bool = is_katakana(furigana)
    if (Ori_bool == True) and (Furi_bool == True): status_code = 1 # 問題なし
    if (Ori_bool == False) and (Furi_bool == True): status_code = 2 # 元のテキストにカタカナ以外が存在．NEologdで正確に読めているか要チェック
    if Furi_bool == False: status_code = -1 # フリガナがカタカナ以外になっているのでレギュレーション違反
    
    return status_code
    
def validate_user_input(user_input):
    # 日本語や英数字のみ許可するバリデーション例
    if re.match(r'^[a-zA-Z0-9ぁ-んァ-ヶー一-龥]+$', user_input):
        return True
    return False


# input_text = '呪術廻旋0'
# print(get_furigana(input_text))
