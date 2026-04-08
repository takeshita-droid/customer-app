"""Google Sheets操作 - 顧客番号の読み取り・更新"""
import sys
sys.path.insert(0, '/Users/takeshitatomoki/.config/google')
from googleapiclient.discovery import build


def get_sheets_service(creds):
    return build('sheets', 'v4', credentials=creds)


def get_next_customer_number(creds, spreadsheet_id):
    """管理シートから次の顧客番号を取得する"""
    service = get_sheets_service(creds)
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='管理シート!B2'
    ).execute()
    value = result.get('values', [[]])[0][0]
    return value.zfill(5)  # 5桁ゼロ埋め（例: "01606"）


def increment_customer_number(creds, spreadsheet_id):
    """管理シートの顧客番号を1増やして保存する"""
    service = get_sheets_service(creds)
    current = get_next_customer_number(creds, spreadsheet_id)
    next_no = str(int(current) + 1).zfill(5)
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range='管理シート!B2',
        valueInputOption='RAW',
        body={'values': [[next_no]]}
    ).execute()
    return next_no
