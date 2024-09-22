import json
import os

dir = os.path.dirname(__file__)

with open(f'{dir}/../raw/itemname_ja.json', encoding='UTF-8') as fin:
    dict = json.load(fin)
    with open(f'{dir}/item_code.json', 'w', encoding='UTF-8') as fout:
        json.dump(dict['itemname'], fout, ensure_ascii=False)
