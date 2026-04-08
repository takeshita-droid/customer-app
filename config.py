"""設定ファイル - 環境変数が優先、なければハードコード値を使用"""
import os

MANAGEMENT_SPREADSHEET_ID = os.environ.get(
    'MANAGEMENT_SPREADSHEET_ID',
    '18wjJ__DQVwB7Kkw4ObzBGrCPAVR1rlGHoArPpPYPEKs'
)

SOURCE_SPREADSHEET_ID = os.environ.get(
    'SOURCE_SPREADSHEET_ID',
    '1jxfEJ0ksC4i4HH4pB9oivTTJ57h0rA3GfuH3bGslSBs'
)

TARGET_FOLDER_ID = os.environ.get(
    'TARGET_FOLDER_ID',
    '1902-4N6toPADJPlCRK5Kcx29Se04YGPn'
)

# 常時ルーム追加したい管理者ID（安定運用メンバー）
CHATWORK_MEMBERS_ADMIN_BASE = [
    379992, 3938728, 6461425, 7905948, 8615577, 8670269,
    8888905, 4849766, 10198096, 9332262, 10711221
]

# まだコンタクト承認待ちのメンバーID
# ここに入っているIDは、APIトークン所有者の contacts に現れた時点で自動復帰する
CHATWORK_MEMBERS_PENDING_APPROVAL = [
]
