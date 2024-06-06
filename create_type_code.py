import json
import re

with open('raw/bundle.js', encoding='UTF-8') as fin:
    ls = re.findall(r'teraType:(.*?)}', fin.read())
    data = ls[0].split(',')
    dict = {}
    for d in data: 
        num = re.sub(r'\D', '', d)
        value = re.findall(r'"(.*?)"', d)[0]
        dict[str(num)] = value
    with open('codelist/type_code.json', 'w', encoding='UTF-8') as fout:
        json.dump(dict, fout, ensure_ascii=False)
    print(dict)
