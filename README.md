# pokemon_home
Pokemon HOME APIを使用してポケモンSVのランクマッチ使用率を取得する。

## 使用技術一覧
<img src="https://img.shields.io/badge/-Python-F2C63C.svg?logo=python&style=for-the-badge">

## ディレクトリ構成
- battle_data : 使用率データの最終出力先
- codelist : APIで取得したデータを日本語名に変換する対応表を格納
- raw : APIやポケモンホーム内部で使われているファイルを格納

## 使い方
```
python update_battle_data.py
```
