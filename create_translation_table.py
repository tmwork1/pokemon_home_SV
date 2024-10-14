import json
import pandas as pd
import re


if __name__ == '__main__':
    with open(f'raw/bundle.js', encoding='utf-8') as fin:
        bundle = fin.read()

    # 言語コードを取得
    for s in re.findall(r'langCode:\[(.*?)]', bundle):
        lang = s.replace('"', '').split(',')
        break
    

    vals = []

    for s in re.findall(r'poke:\[(.*?)]', bundle):
        vals.append(s.replace('"', '').split(','))

    df = pd.DataFrame(vals, index=lang, columns=list(range(1, len(vals[0])+1)))

    # json出力
    with open(f'output/name.json', 'w', encoding='utf-8') as fout:
        fout.write(df.to_json(force_ascii=False))

    # csv出力
    with open(f'output/name.csv', 'w', encoding='utf-8') as fout:
        df.T.to_csv(fout, lineterminator='\n')


    tags = ['tokusei', 'waza']
    files = ['ability', 'move']

    for tag, file in zip(tags, files):
        vals = []

        for s in re.findall(fr'{tag}:{{(.*?)}}', bundle):
            vals.append(s.split('",'))
            vals[-1] = [v.replace('"', '') for v in vals[-1]]
            vals[-1] = [v[v.index(':')+1:] for v in vals[-1]]

        df = pd.DataFrame(vals, index=lang, columns=list(range(1, len(vals[0])+1)))

        # json出力
        with open(f'output/{file}.json', 'w', encoding='utf-8') as fout:
            fout.write(df.to_json(force_ascii=False))

        # csv出力
        with open(f'output/{file}.csv', 'w', encoding='utf-8') as fout:
            df.T.to_csv(fout, lineterminator='\n')
