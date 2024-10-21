import requests
import json
import os
import re
import pandas as pd
from copy import deepcopy

def create_type_code():
    with open(f'raw/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'teraType:(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data: 
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_nature_code():
    with open(f'raw/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'seikaku:(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data: 
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_ability_code():
    with open(f'raw/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'tokusei:(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data: 
            num = re.sub(r'\D', '', d)
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_move_code():
    with open(f'raw/bundle.js', encoding='utf-8') as fin:
        ls = re.findall(r'waza:{(.*?)}', fin.read())
        data = ls[0].split(',')
        dict = {}
        for d in data:
            num = d[:d.index(':')]
            value = re.findall(r'"(.*?)"', d)[0]
            dict[str(num)] = value
    return dict

def create_item_code():
    with open(f'raw/itemname_ja.json', encoding='utf-8') as fin:
        return json.load(fin)['itemname']


if __name__ == '__main__':
    #-------------------------------------------------------------
    # シーズン（最新: 0, 前シーズン: 1, 前前シーズン: 2, ...）
    season_idx = 0

    # ルール（シングル: 0, ダブル: 1）
    rule = 0
    #-------------------------------------------------------------

    dir = os.path.dirname(__file__)

    # 図鑑の読み込み
    with open("output/zukan.json", encoding='utf-8') as fin:
        zukan = json.load(fin)

    # デコードデータの読み込み
    type_code = create_type_code()
    nature_code = create_nature_code()
    ability_code = create_ability_code()
    move_code = create_move_code()
    item_code = create_item_code()

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'countrycode': '304',
        'authorization': 'Bearer',
        'langcode': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
        'content-type': 'application/json',
    }

    # シーズン情報を取得
    print('通信中...')
    #url = 'https://api.battle.pokemon-home.com/cbd/competition/rankmatch/list' # 剣盾
    url = 'https://api.battle.pokemon-home.com/tt/cbd/competition/rankmatch/list' # SV
    res = requests.post(url, headers=headers, data='{"soft":"Sw"}')
    with open(f'{dir}/raw/season.json', 'w', encoding='utf-8') as fout:
        fout.write(res.text)
    data = json.loads(res.text)['list']
    current_season = list(data.keys())[season_idx]

    terms = []
    for sn in data:
        for id in data[sn]:
            if data[sn][id]['rule'] == rule:
                terms.append({'id': id, 'rst': data[sn][id]['rst'], 'ts1': data[sn][id]['ts1'], 'ts2': data[sn][id]['ts2']})

    term = terms[season_idx]
    id, rst, ts1, ts2 = term['id'], term['rst'], term['ts1'], term['ts2']
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Mobile Safari/537.36',
        'content-type': 'application/json',
    }

    # ポケモンの使用率を取得
    #url = f'https://resource.pokemon-home.com/battledata/ranking/{id}/{rst}/{ts2}/pokemon' # 剣盾
    url = f'https://resource.pokemon-home.com/battledata/ranking/scvi/{id}/{rst}/{ts2}/pokemon' # SV
    res = requests.get(url, headers=headers)
    with open(f'{dir}/raw/pokemon_rank.json', 'w', encoding='utf-8') as fout:
        fout.write(res.text)
    data = json.loads(res.text)
    rank = {}
    for i,d in enumerate(data):
        rank[f"{d['id']:04}-{d['form']:03}"] = i + 1

    # 採用率を取得
    for x in range(1,7):
        #url = f'https://resource.pokemon-home.com/battledata/ranking/{id}/{rst}/{ts2}/pdetail-{x}' # 剣盾
        url = f'https://resource.pokemon-home.com/battledata/ranking/scvi/{id}/{rst}/{ts2}/pdetail-{x}' # SV
        res = requests.get(url, headers=headers)
        with open(f'{dir}/raw/pokemon_{x}.json', 'w', encoding='utf-8') as fout:
            fout.write(res.text)

    # 採用率 (図鑑番号順)
    adoption = {}
    for x in range(1,7):
        with open(f'{dir}/raw/pokemon_{x}.json', encoding='utf-8') as fin:
            data = json.load(fin)

        for id in data:
            for form_id in data[id]:
                key = f"{int(id):04}-{int(form_id):03}"
                if key not in zukan:
                    print(f"{key} is not in zukan")
                    continue

                adoption[key] = {'rank': rank[key] if key in rank else 9999}

                for k in ['id','form_id','name','form','alias']:
                    adoption[key][k] = zukan[key][k]

                # 技
                adoption[key]['move'], adoption[key]['move_rate'] = [], []
                for d in data[id][form_id]['temoti']['waza']:
                    adoption[key]['move'].append(move_code[str(d['id'])])
                    adoption[key]['move_rate'].append(float(d['val']))

                # 性格
                adoption[key]['nature'], adoption[key]['nature_rate'] = [], []
                for d in data[id][form_id]['temoti']['seikaku']:
                    adoption[key]['nature'].append(nature_code[str(d['id'])])
                    adoption[key]['nature_rate'].append(float(d['val']))

                # 特性
                adoption[key]['ability'], adoption[key]['ability_rate'] = [], []
                for d in data[id][form_id]['temoti']['tokusei']:
                    adoption[key]['ability'].append(ability_code[str(d['id'])])
                    adoption[key]['ability_rate'].append(float(d['val']))
                
                # アイテム
                adoption[key]['item'], adoption[key]['item_rate'] = [], []
                for d in data[id][form_id]['temoti']['motimono']:
                    adoption[key]['item'].append(item_code[str(d['id'])])
                    adoption[key]['item_rate'].append(float(d['val']))
                
                # テラスタイプ
                adoption[key]['terastal'], adoption[key]['terastal_rate'] = [], []
                for d in data[id][form_id]['temoti']['terastal']:
                    adoption[key]['terastal'].append(type_code[str(d['id'])])
                    adoption[key]['terastal_rate'].append(float(d['val']))

    # オーガポンの使用率を修正
    if "1017-000" in adoption:
        # みどりのめん以外
        form_id = 1
        while True:
            key = f"1017-{form_id:03}"
            if key not in zukan:
                break
            adoption[key] = deepcopy(adoption["1017-000"])
            for k in ['id','form_id','name','form','alias']:
                adoption[key][k] = zukan[key][k]
            adoption[key]['ability'] = [zukan[key]['ability_1']]
            adoption[key]['ability_rate'] = [100.]
            adoption[key]['item'] = [zukan[key]['form']]
            adoption[key]['item_rate'] = [100.]
            adoption[key]['terastal'] = [zukan[key]['type_2']]
            adoption[key]['terastal_rate'] = [100.0]
            form_id += 1

        # みどりのめん
        key = "1017-000"
        adoption[key]['ability'] = [zukan[key]['ability_1']]
        adoption[key]['terastal'] = [zukan[key]['type_1']]
        items, item_rates = [], []
        for item, rate in zip(adoption[key]['item'], adoption[key]['item_rate']):
            if 'のめん' in item:
                continue
            items.append(item)
            item_rates.append(rate)

        item_rates = [round(100*v/sum(item_rates), 1) for v in item_rates] # 規格化
        adoption[key]['item'], adoption[key]['item_rate'] = items, item_rates

    # 使用率順に並び替える
    df = pd.DataFrame(adoption).T
    df = df.sort_values(['rank','form_id'])
    
    # json出力
    with open(f"{dir}/output/season{current_season}.json", 'w', encoding='utf-8') as fout:
        fout.write(df.T.to_json())

    # csv出力
    with open(f'output/season{current_season}.csv', 'w', encoding='utf-8') as fout:
        df.to_csv(fout, lineterminator='\n')
