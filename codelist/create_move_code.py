import json
import re
import os

dir = os.path.dirname(__file__)

with open(f'{dir}/../raw/bundle.js', encoding='UTF-8') as fin:
    ls = re.findall(r'waza:{(.*?)}', fin.read())
    data = ls[0].split(',')
    dict = {}
    for d in data:
        num = d[:d.index(':')]
        value = re.findall(r'"(.*?)"', d)[0]
        dict[str(num)] = value
    with open(f'{dir}/move_code.json', 'w', encoding='UTF-8') as fout:
        json.dump(dict, fout, ensure_ascii=False)
    print(dict)
