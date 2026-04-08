"""Chatwork API操作 - グループルームの作成"""
import os
import requests


def get_token():
    token = os.environ.get('CHATWORK_API_TOKEN')
    if not token:
        env_path = os.path.expanduser('~/.config/api-keys.env')
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith('CHATWORK_API_TOKEN='):
                    token = line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
    if not token:
        raise ValueError("Chatwork APIトークンが見つかりません")
    return token


def get_contact_ids(token):
    """コンタクトリストのアカウントIDセットを返す"""
    headers = {'X-ChatWorkToken': token}
    response = requests.get('https://api.chatwork.com/v2/contacts', headers=headers)
    if response.status_code != 200:
        return set()
    return {str(c['account_id']) for c in response.json()}


def get_my_account_id(token):
    """APIトークン所有者自身のアカウントIDを取得する"""
    headers = {'X-ChatWorkToken': token}
    response = requests.get('https://api.chatwork.com/v2/me', headers=headers)
    if response.status_code != 200:
        raise Exception(f"自分のアカウント取得失敗: {response.text}")
    return response.json()['account_id']


def create_chatwork_group(room_name, description, admin_member_ids):
    """
    Chatworkグループを作成する。
    コンタクト未登録のメンバーは除外し、別途リストで返す。
    返り値: (room_id, room_url, added_ids, skipped_ids)
    """
    token = get_token()
    headers = {'X-ChatWorkToken': token}

    # 自分自身のIDは常に含める（コンタクトリスト外でもルーム作成に必須）
    my_id = get_my_account_id(token)

    # コンタクト登録済みのみ絞り込む（自分は除外して別途追加）
    contacts = get_contact_ids(token)
    available = [m for m in admin_member_ids if str(m) in contacts and m != my_id]
    skipped = [m for m in admin_member_ids if str(m) not in contacts and m != my_id]

    # 自分を先頭に追加
    available = [my_id] + available

    members_admin = ','.join(str(m) for m in available)

    data = {
        'name': room_name,
        'description': description,
        'members_admin_ids': members_admin,
    }

    response = requests.post(
        'https://api.chatwork.com/v2/rooms',
        headers=headers,
        data=data
    )

    if response.status_code != 200:
        raise Exception(f"Chatworkルーム作成失敗: {response.status_code} {response.text}")

    room_id = response.json()['room_id']
    room_url = f"https://www.chatwork.com/#!rid{room_id}"
    print(f"✅ Chatworkグループ作成完了: {room_name}")
    print(f"   ルームID: {room_id}  追加済み: {available}  未追加: {skipped}")
    return room_id, room_url, available, skipped
