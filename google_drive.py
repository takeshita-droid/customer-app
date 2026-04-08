"""Google Drive操作 - 資金計画スプレッドシートのコピー"""
import sys
sys.path.insert(0, '/Users/takeshitatomoki/.config/google')
from googleapiclient.discovery import build


def get_drive_service(creds):
    return build('drive', 'v3', credentials=creds)


def copy_shikin_plan(creds, source_spreadsheet_id, customer_no, target_folder_id):
    """
    資金計画スプレッドシートをコピーし、顧客番号でリネームして指定フォルダに保存する。
    返り値: コピーしたスプレッドシートのURL
    """
    service = get_drive_service(creds)

    # 元ファイルのメタデータ取得（ファイル名確認）
    file_meta = service.files().get(
        fileId=source_spreadsheet_id,
        fields='name',
        supportsAllDrives=True
    ).execute()
    original_name = file_meta['name']

    # ファイル名の先頭 "0000" を顧客番号に置換
    if '0000' in original_name:
        new_name = original_name.replace('0000', customer_no, 1)
    else:
        new_name = f"{customer_no}_{original_name}"

    # ファイルをコピー（指定フォルダへ）
    copied = service.files().copy(
        fileId=source_spreadsheet_id,
        body={
            'name': new_name,
            'parents': [target_folder_id]
        },
        supportsAllDrives=True
    ).execute()

    new_id = copied['id']
    url = f"https://docs.google.com/spreadsheets/d/{new_id}/edit"
    print(f"✅ 資金計画コピー完了: {new_name}")
    print(f"   URL: {url}")
    return url, new_name
