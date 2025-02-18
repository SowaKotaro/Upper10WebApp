# 参考：yucatio@システムエンジニア 様
# https://yucatio.hatenablog.com/entry/2019/12/18/214251

# 辞書順ルール
# 1. 清音 -> 濁音 -> 半濁音     ex.) ホール->ボール->ポール
# 2. 大文字 -> 小文字           ex.) ねつき->ねっき，じゆう->じゅう
# 3. 長音は直前の母音として扱う  ex.) カード => カアド

SMALL_TO_NORMAL = {
    'ァ': 'ア', 'ィ': 'イ', 'ゥ': 'ウ', 'ェ': 'エ', 'ォ': 'オ',
    'ッ': 'ツ',
    'ャ': 'ヤ', 'ュ': 'ユ', 'ョ': 'ヨ',
    'ヮ': 'ワ',
}

VU_TO_U = {
    'ヴ': 'ウ',
}

CHOUON_TO_BOIN = {
    'ア': 'ア', 'イ': 'イ', 'ウ': 'ウ', 'エ': 'エ', 'オ': 'オ',
    'ァ': 'ア', 'ィ': 'イ', 'ゥ': 'ウ', 'ェ': 'エ', 'ォ': 'オ',
    'ヴ': 'ウ',
    'カ': 'ア', 'キ': 'イ', 'ク': 'ウ', 'ケ': 'エ', 'コ': 'オ',
    'ガ': 'ア', 'ギ': 'イ', 'グ': 'ウ', 'ゲ': 'エ', 'ゴ': 'オ',
    'サ': 'ア', 'シ': 'イ', 'ス': 'ウ', 'セ': 'エ', 'ソ': 'オ',
    'ザ': 'ア', 'ジ': 'イ', 'ズ': 'ウ', 'ゼ': 'エ', 'ゾ': 'オ',
    'タ': 'ア', 'チ': 'イ', 'ツ': 'ウ', 'テ': 'エ', 'ト': 'オ',
    'ダ': 'ア', 'ヂ': 'イ', 'ヅ': 'ウ', 'デ': 'エ', 'ド': 'オ',
    'ナ': 'ア', 'ニ': 'イ', 'ヌ': 'ウ', 'ネ': 'エ', 'ノ': 'オ',
    'ハ': 'ア', 'ヒ': 'イ', 'フ': 'ウ', 'ヘ': 'エ', 'ホ': 'オ',
    'バ': 'ア', 'ビ': 'イ', 'ブ': 'ウ', 'ベ': 'エ', 'ボ': 'オ',
    'パ': 'ア', 'ピ': 'イ', 'プ': 'ウ', 'ペ': 'エ', 'ポ': 'オ',
    'マ': 'ア', 'ミ': 'イ', 'ム': 'ウ', 'メ': 'エ', 'モ': 'オ',
    'ヤ': 'ア', 'ユ': 'ウ', 'ヨ': 'オ',
    'ャ': 'ア', 'ュ': 'ウ', 'ョ': 'オ',
    'ラ': 'ア', 'リ': 'イ', 'ル': 'ウ', 'レ': 'エ', 'ロ': 'オ',
    'ワ': 'ア', 'ヰ': 'イ', 'ヱ': 'エ', 'ヲ': 'オ',
    'ヮ': 'ア',
}
def replace_chouon_with_vowel(records): # 長音を直前の文字の母音に変換
    for reocrd in records:
        result = []
        last_vowel = ''  # 直前の母音を保持するための変数
        for char in reocrd[2]:
            if char == 'ー':  # 長音記号が見つかった場合
                if last_vowel:  # 直前の母音がある場合
                    result.append(last_vowel)
                else:
                    result.append('ー')  # 最初の文字が長音記号だった場合
            else:
                result.append(char)
                # 直前の文字が母音に対応するかチェック
                if char in CHOUON_TO_BOIN:
                    last_vowel = CHOUON_TO_BOIN[char]  # 直前の母音を更新
        reocrd.append(''.join(result))
    return records
# ソート用のカスタム関数
def custom_sort_key(word):
    new_word = []
    for char in word:
        # 小さい文字を見つけたら、その対応する大きい文字に変換し、特殊な文字を追加してソート順を調整
        if char in VU_TO_U:
            new_word.append(VU_TO_U[char] + '2')
        if char in SMALL_TO_NORMAL:
            # 大きい文字の後に小さい文字が並ぶように調整
            new_word.append(SMALL_TO_NORMAL[char] + '1')  # 小さい文字は「1」を追加して大きい文字の後に来るように
        else:
            new_word.append(char + '0')  # 通常の文字は「0」を追加して通常の順番に
    # print(word, new_word)
    return ''.join(new_word)

def sort_dict(records, ascending):
    records = replace_chouon_with_vowel(records)
    records.sort(reverse=ascending, key=lambda x: custom_sort_key(x[-1]))
    for item in records:
        item = item[:6]
    # print(records, "aaaaaa")
    return records

def sort_len(records, ascending):
    records = sorted(records, reverse=ascending, key=lambda x: x[3])
    return records

def sort_id(records, ascending):
    records = sorted(records, reverse=ascending, key=lambda x: x[0])
    return records