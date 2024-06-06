import json
import re

# フォルム名の修正
def modifyForm(s):
    #print(s, end='\t')
    s = s.replace('あかいろの', '')
    s = s.replace('ファンシーなもよう', '')
    s = s.replace('すじ', '')
    s = s.replace('スタイル', '')
    s = s.replace('じょうのすがた', '')
    s = s.replace('たすがた', '')
    s = s.replace('なすがた', '')
    s = s.replace('のすがた', '')
    s = s.replace('のかた', '')
    s = s.replace('のたてがみ', '')
    s = s.replace('のつばさ', '')
    s = s.replace('のミノ', '')
    s = s.replace('のめん', '')
    s = s.replace('のもよう', '')
    s = s.replace('のゆうしゃ', '')
    s = s.replace('フォルム', '')
    s = s.replace('フェイス', '')
    s = s.replace('フーパ', '')
    s = s.replace('もよう', '')
    s = s.replace('モード', '')
    #print(s)
    return s

def modifyName(s):
    if 'ロトム(' in s:
        s = s[s.index('(')+1:s.index(')')]
    if 'キュレム)' in s:
        s = s[s.index('(')+1:s.index(')')]
    for v in ['アローラ','ガラル','ヒスイ','パルデア']:
        if v in s:
            s = v + s.replace('('+v+')', '')
            break
    if 'イルカマン' in s:
        s = 'イルカマン(マイティ)'
    if s == 'パルデアケンタロス':
        s = 'パルデアケンタロス(かくとう)'
    return s


with open('raw/bundle.js', encoding='UTF-8') as fin:
    ls = re.findall(r'poke:\[(.*?)\]', fin.read())
    names = ls[0].split(',')

with open('raw/zkn_form_ja_modified.json', encoding='UTF-8') as fin:
    dict = json.load(fin)
    forms = {}
    for key in dict['zkn_form'].keys():
        id = str(int(key[:-4]))
        form_num = str(int(key[-3:]))
        if id not in forms:
            forms[id] = {}
        forms[id][form_num] = modifyForm(dict['zkn_form'][key])

id = 1
dict = {}
for name in names:
    name = name[1:-1] #""を除去
    if str(id) not in forms:
        dict[str(id)] = {'0': name}
    else:
        dict[str(id)] = {'0': name} if '0' not in forms[str(id)] else {}
        for form_num in forms[str(id)]:
            dict[str(id)][str(form_num)] = name
            if forms[str(id)][form_num] != '':
                dict[str(id)][str(form_num)] += '(' + forms[str(id)][form_num] + ')'
    
    for key in dict[str(id)]:
        dict[str(id)][key] = modifyName(dict[str(id)][key])

    print(id, dict[str(id)])
    id += 1

with open('codelist/name_code.json', 'w', encoding='UTF-8') as fout:
    json.dump(dict, fout, ensure_ascii=False)