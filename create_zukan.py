from alias import *
import json
import re
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
import mojimoji


def read_HOME() -> dict:
    """ポケモンHOMEの内部データをもとに図鑑の辞書を作成"""
    # 名前を読み込む
    with open(f'raw/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'poke:\[(.*?)\]', fin.read())
        names = ls[0].split(',')
        names = [s[1:-1] for s in names] # ""を除去

    # フォルムを読み込む
    with open(f'raw/zkn_form_ja.json', encoding='utf-8') as fin:
        dict = json.load(fin)
        forms = {}
        for key in dict['zkn_form'].keys():
            if not key[:3].isdigit() or len(key) > 8:
                continue
            d = key.index('_')
            id = str(int(key[:d]))
            form_id = str(int(key[d+1:d+4]))
            if id not in forms:
                forms[id] = {}
            forms[id][form_id] = dict['zkn_form'][key]

    # zkn_form_ja.jsonに含まれないフォルムを追加
    other_forms = {
        'コオリッポ': ['アイスフェイス', 'ナイスフェイス'],
        'イルカマン': ['ナイーブフォルム', 'マイティフォルム'],
        'シャリタツ': ['そったすがた', 'たれたすがた', 'のびたすがた'],
        'オーガポン': ['みどりのめん', 'いどのめん', 'かまどのめん', 'いしずえのめん'],
    }
    for name in other_forms:
        id = names.index(name) + 1
        forms[str(id)] = {}
        for form_id, form in enumerate(other_forms[name]):
            forms[str(id)][str(form_id)] = form

    # 辞書に格納. key = "図鑑番号(4桁)-フォルム番号(3桁)"
    zukan = {}

    for i,name in enumerate(names):
        id = i + 1

        key = f"{id:04}-{0:03}"
        zukan[key] = {}
        aliases = []

        if str(id) not in forms or '0' not in forms[str(id)]:
            zukan[key]['id'] = id
            zukan[key]['form_id'] = 0
            zukan[key]['name'] = name
            zukan[key]['form'] = ''
            zukan[key]['alias'] = alias(zukan[key])
            aliases.append(zukan[key]['alias'])

        # フォルム違いがある場合
        if str(id) in forms:
            for form_id in forms[str(id)]:
                key = f"{id:04}-{int(form_id):03}"
                dict = {}
                dict['id'] = id
                dict['form_id'] = int(form_id)
                dict['name'] = name
                dict['form'] = forms[str(id)][form_id]
                dict['alias'] = alias(dict)

                # aliasが重複していればスキップ
                if dict['alias'] in aliases:
                    print(f"{dict['alias']} {dict['form']} が重複しているためスキップ")
                    continue

                zukan[key] = dict
                aliases.append(dict['alias'])

    return zukan

def read_official_zukan(zukan: dict):
    """公式の図鑑サイトから情報を取得"""
    # 公式の図鑑サイトで使われているタイプコードを読み込む
    with open(f'raw/zukan_type.json', encoding='utf-8') as fin:
        zukan_types = [''] + list(json.load(fin).keys())

    # 公式の図鑑にない情報
    bakeccha_weight = {'ちいさいサイズ': 3.5,'ふつうのサイズ': 5,'おおきいサイズ': 7.5,'とくだいサイズ': 15}
    bakeccha_height = {'ちいさいサイズ': 0.3,'ふつうのサイズ': 0.4,'おおきいサイズ': 0.5,'とくだいサイズ': 0.8}

    panpujin_weight = {'ちいさいサイズ': 9.5,'ふつうのサイズ': 12.5,'おおきいサイズ': 14,'とくだいサイズ': 39}
    panpujin_height = {'ちいさいサイズ': 0.7,'ふつうのサイズ': 0.9,'おおきいサイズ': 1.1,'とくだいサイズ': 1.7}

    # 公式の図鑑サイトから情報を取得
    prev_id, prev_form_id = 0, 0

    for key, dict in zukan.items():
        # 初期化
        zukan[key]['category'] = ''
        zukan[key]['weight'] = 0
        zukan[key]['height'] = 0
        for k in ['type_1', 'type_2']:
            zukan[key][k] = ''
        for k in ['ability_1', 'ability_2', 'ability_3']:
            zukan[key][k] = ''

        url = f"https://zukan.pokemon.co.jp/detail/{dict['id']:04}"

        form_id = dict['form_id']
        if form_id > 0:
            if dict['id'] == prev_id and form_id != prev_form_id + 1:
                form_id = prev_form_id + 1
            url += f"-{form_id}"

        try:
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            s = soup.find(id='json-data').get_text()
        except:
            print(f"{dict['alias']}: Failed to access {url}")
            continue
        
        s = s[s.index('{'):s.rindex('}')+1]
        d = json.loads(s)

        zukan[key]['category'] = d['pokemon']['bunrui']
        zukan[key]['weight'] = d['pokemon']['omosa']
        zukan[key]['height'] = d['pokemon']['takasa']
        for k in ['type_1', 'type_2']:
            zukan[key][k] = zukan_types[d['pokemon'][k]]

        if zukan[key]['name'] == 'バケッチャ':
            zukan[key]['weight'] = bakeccha_weight[zukan[key]['form']]
            zukan[key]['height'] = bakeccha_height[zukan[key]['form']]
        elif zukan[key]['name'] == 'パンプジン':
            zukan[key]['weight'] = panpujin_weight[zukan[key]['form']]
            zukan[key]['height'] = panpujin_height[zukan[key]['form']]

        for i,da in enumerate(d['abilities']):
            zukan[key][f"ability_{i+1}"] = da['name']

        print(zukan[key])
        prev_id, prev_form_id = dict['id'], form_id

def read_wiki(zukan):
    """ポケモンWikiから特性と種族値を取得"""
    ### 特性
    url = "https://wiki.xn--rckteqa2e.com/wiki/%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%81%AE%E3%81%A8%E3%81%8F%E3%81%9B%E3%81%84%E4%B8%80%E8%A6%A7"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table')

    abbr = {
        'A': 'アローラのすがた',
        'G': 'ガラルのすがた',
        'H': 'ヒスイのすがた',
        'P': 'パルデアのすがた',
    }

    for i,tr in enumerate(table.find_all('tr')):
        if i == 0:
            continue
        
        data = [td.text.strip() for td in tr.find_all('td')]
        #print(data)

        # 名前とフォルムを取得
        name, form = data[1], ''

        if '(' in name:
            name = data[1][:data[1].index('(')]
            form = data[1][data[1].index('(')+1:-1]

        if name[-1] in ['A','G','H','P']:
            form = abbr[name[-1]]
            name = name[:-1]

        for mark, s in zip(['♂','♀'], ['オスのすがた','メスのすがた']):
            if name[-1] == mark and 'ニドラン' not in name:
                name = name[:-1]
                form = s

        name = mojimoji.han_to_zen(name)
        form = mojimoji.han_to_zen(form)

        if name in ['カラナクシ','トリトドン','シキジカ','メブキジカ']:
            form = ''

        # 図鑑に追加
        for key, d in zukan.items():
            matched = d['name'] == name
            if form:
                matched &= d['form'] == form

            if matched:
                abilities = [zukan[key][f"ability_{j+1}"] for j in range(3) if zukan[key][f"ability_{j+1}"]]
                for ability in data[2:5]:
                    if len(abilities) == 3:
                        break
                    if not ability:
                        continue

                    for s in ['*', '[']:
                        if s in ability:
                            ability = ability[:ability.index(s)]
                    if ability not in abilities:
                        zukan[key][f"ability_{len(abilities)+1}"] = ability
                        print(zukan[key]['alias'], ability, '追加')

    ### 種族値
    # 初期化
    labels = ['H','A','B','C','D','S']
    for key in zukan:
        zukan[key]['last_gen'] = 0
        for j in range(3):
            zukan[key][labels[j]] = ''

    # 古い世代から順にすべて参照する
    urls = [
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B8%80%E4%B8%96%E4%BB%A3)',
        '',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B8%89%E4%B8%96%E4%BB%A3)',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E5%9B%9B%E4%B8%96%E4%BB%A3)',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%BA%94%E4%B8%96%E4%BB%A3)',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E5%85%AD%E4%B8%96%E4%BB%A3)',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B8%83%E4%B8%96%E4%BB%A3)',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E5%85%AB%E4%B8%96%E4%BB%A3)',
        'https://wiki.xn--rckteqa2e.com/wiki/%E7%A8%AE%E6%97%8F%E5%80%A4%E4%B8%80%E8%A6%A7_(%E7%AC%AC%E4%B9%9D%E4%B8%96%E4%BB%A3)',
    ]

    zukan_names = [d['name'] for d in zukan.values()]

    for g, url in enumerate(urls):
        if not url:
            continue

        print(url)
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')

        for i,tr in enumerate(table.find_all('tr')):
            if i == 0:
                continue
            
            data = [td.text.strip() for td in tr.find_all(['th','td'])]
            #print(data)

            # 名前とフォルムを取得
            name, form = data[1], ''

            if '(' in name:
                name = data[1][:data[1].index('(')]
                form = data[1][data[1].index('(')+1:-1]

            if '・' in form:
                form = form[:form.index('・')]

            for mark, s in zip(['♂','♀'], ['オスのすがた','メスのすがた']):
                if name[-1] == mark and 'ニドラン' not in name:
                    name = name[:-1]
                    form = s

            if name == 'メテノ' and 'コア' in form:
                form = 'あかいろのコア'

            if name == 'フーパ':
                form = form.replace('すがた', 'フーパ')

            if len(name) > 6:
                for n in range(3, 7):
                    if name[:n] in zukan_names:
                        form = name[n:]
                        name = name[:n]
                        break

            name = mojimoji.han_to_zen(name)
            form = mojimoji.han_to_zen(form)

            # 図鑑に追加
            for key, d in zukan.items():
                matched = d['name'] == name
                if form:
                    matched &= d['form'] == form
                if matched:
                    zukan[key]['last_gen'] = g + 1
                    for j,v in enumerate(data[4:10]):
                        zukan[key][labels[j]] = v

def dump(zukan):
    # json出力
    with open(f'output/zukan.json', 'w', encoding='utf-8') as fout:
        json.dump(zukan, fout, ensure_ascii=False)

    # csv出力
    with open(f'output/zukan.csv', 'w', encoding='utf-8') as fout:
        df = pd.DataFrame(zukan)
        df.T.to_csv(fout, lineterminator='\n')


if __name__ == '__main__':
    #"""
    # 1.ポケモンHOMEの内部データから辞書を生成
    zukan = read_HOME()
    dump(zukan) # 途中経過

    # 2.公式の図鑑サイトから情報を取得 (かなり時間がかかる)
    read_official_zukan(zukan)
    dump(zukan) # 途中経過
    #"""

    # 3.ポケモンWikiから夢特性と種族値を取得 (すこし時間がかかる)
    """
    with open(f'output/zukan.json', encoding='utf-8') as fin:
        # 途中保存から再開
        zukan = json.load(fin)
    """
    read_wiki(zukan)
    dump(zukan) # 最終出力
