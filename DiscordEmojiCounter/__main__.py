"""
TODO - 設定ファイルを指定して実行できるようにする
"""

#!/usr/bin/env python3
#-*- coding:utf-8 -*-
import json
from .Bot import *
from pathlib import Path

# 設定ファイルのテンプレート
SERVER_SECRET_TEMPLATE = {
    'discord_token': 'your token here'
}

# data/ServerSecret.jsonが設定ファイル
path = Path('data/ServerSecret.json')

if path.exists():
    # ファイルがあればロードする
    with path.open(mode='r') as f:
        server_secret = json.load(f)
else:
    # ファイルがなければ、テンプレートをコピーして作成する
    with path.open(mode='w') as f:
        json.dump(SERVER_SECRET_TEMPLATE, f, ensure_ascii=False, indent=4)
    print(u'data/ServerSecret.jsonを生成しました。')
    print(u'必要な情報を入力して、再実行してください。')
    exit()

# 走らせる
Bot('data').run(server_secret['discord_token'])
