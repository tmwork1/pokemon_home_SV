import json

with open('raw/itemname_ja.json', encoding='UTF-8') as fin:
    dict = json.load(fin)
    with open('codelist/item_code.json', 'w', encoding='UTF-8') as fout:
        json.dump(dict['itemname'], fout, ensure_ascii=False)
