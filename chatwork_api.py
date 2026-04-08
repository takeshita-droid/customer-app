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
    if response.status_code == 204:
        return set()
    if response.status_code != 200:
        raise Exception(
            f"Chatworkコンタクト取得失敗: HTTP {response.status_code} {response.text}\n"
            "APIトークンにコンタクト読み取り権限があるか、発行元アカウントを確認してください。"
        )
    data = response.json()
    if not isinstance(data, list):
        raise Exception(f"Chatworkコンタクト取得: 想定外のレスポンス: {data!r}")
    return {str(c['account_id']) for c in data}


def get_my_account_id(token):
    """APIトークン所有者自身のアカウントIDを取得する"""
    headers = {'X-ChatWorkToken': token}
    response = requests.get('https://api.chatwork.com/v2/me', headers=headers)
    if response.status_code != 200:
        raise Exception(f"自分のアカウント取得失敗: {response.text}")
    return response.json()['account_id']


def debug_members_vs_contacts(admin_member_ids):
    """
    トークン所有者の account_id と、指定メンバーが GET /contacts に載るかを返す。
    「コンタクト登録したのにスキップされる」調査用。
    """
    token = get_token()
    my_id = get_my_account_id(token)
    contacts = get_contact_ids(token)
    want = [m for m in admin_member_ids if m != my_id]
    in_contacts = [m for m in want if str(m) in contacts]
    missing = [m for m in want if str(m) not in contacts]
    return {
        'token_owner_account_id': my_id,
        'contact_count': len(contacts),
        'requested_member_ids': want,
        'in_contacts': in_contacts,
        'not_in_contacts_api': missing,
    }


def resolve_admin_member_ids(base_member_ids, pending_member_ids=None):
    """
    常時追加メンバー + 承認待ちメンバーを解決する。
    承認待ちは contacts に載ったIDのみ自動復帰する。
    """
    token = get_token()
    my_id = get_my_account_id(token)
    contacts = get_contact_ids(token)

    pending_member_ids = pending_member_ids or []
    recovered_pending = [m for m in pending_member_ids if str(m) in contacts and m != my_id]
    still_pending = [m for m in pending_member_ids if str(m) not in contacts and m != my_id]

    target_admin_ids = _unique_admin_ids(my_id, base_member_ids + recovered_pending)
    return {
        'token_owner_account_id': my_id,
        'target_admin_ids': target_admin_ids,
        'recovered_pending_ids': recovered_pending,
        'still_pending_ids': still_pending,
    }


def _unique_admin_ids(my_id, admin_member_ids):
    """自分を先頭に、重複なしで並べる"""
    out = [my_id]
    seen = {my_id}
    for m in admin_member_ids:
        if m == my_id or m in seen:
            continue
        seen.add(m)
        out.append(m)
    return out


def create_chatwork_group(room_name, description, base_member_ids, pending_member_ids=None):
    """
    Chatworkグループを作成する。
    公式ではメンバーは「コンタクト済みまたは同一組織内」。
    まずは設定の全IDで作成を試し、失敗した場合のみコンタクト一覧で絞り込む。
    返り値: (room_id, room_url, added_ids, skipped_ids)
    """
    token = get_token()
    headers = {'X-ChatWorkToken': token}

    resolved = resolve_admin_member_ids(base_member_ids, pending_member_ids)
    my_id = resolved['token_owner_account_id']
    full_list = resolved['target_admin_ids']
    still_pending = resolved['still_pending_ids']
    members_admin_full = ','.join(str(m) for m in full_list)

    data_full = {
        'name': room_name,
        'description': description,
        'members_admin_ids': members_admin_full,
    }

    response = requests.post(
        'https://api.chatwork.com/v2/rooms',
        headers=headers,
        data=data_full,
    )

    if response.status_code == 200:
        room_id = response.json()['room_id']
        room_url = f"https://www.chatwork.com/#!rid{room_id}"
        print(f"✅ Chatworkグループ作成完了: {room_name}")
        print(f"   ルームID: {room_id}  管理者: {full_list}")
        if still_pending:
            print(f"   保留中(contacts未承認): {still_pending}")
        return room_id, room_url, full_list, still_pending

    err_full = response.text

    contacts = get_contact_ids(token)
    requested = [m for m in base_member_ids + (pending_member_ids or []) if m != my_id]
    available = [m for m in requested if str(m) in contacts]
    skipped = [m for m in requested if str(m) not in contacts]
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
        data=data,
    )

    if response.status_code != 200:
        raise Exception(
            f"Chatworkルーム作成失敗（全員指定）: {err_full}\n"
            f"フォールバック後も失敗: HTTP {response.status_code} {response.text}"
        )

    room_id = response.json()['room_id']
    room_url = f"https://www.chatwork.com/#!rid{room_id}"
    print(f"✅ Chatworkグループ作成完了: {room_name}")
    print(f"   ルームID: {room_id}  追加済み: {available}  未追加: {skipped}")
    return room_id, room_url, available, skipped
