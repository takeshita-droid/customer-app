"""
サーバー用Google認証モジュール。
環境変数 GOOGLE_TOKEN_JSON からトークンを読み込む（Render等のクラウド用）。
ローカルではファイルベースの認証にフォールバック。
"""
import os
import json
import sys
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def authenticate():
    token_json_str = os.environ.get('GOOGLE_TOKEN_JSON')

    if token_json_str:
        # 本番環境：環境変数からトークンを読み込む
        token_data = json.loads(token_json_str)
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds
    else:
        # ローカル環境：ファイルベースの認証
        sys.path.insert(0, '/Users/takeshitatomoki/.config/google')
        from auth import authenticate as local_auth
        return local_auth()
