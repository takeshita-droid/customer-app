"""新規顧客登録Webアプリ - メインサーバー"""
import os
from flask import Flask, render_template, jsonify, request, session
from auth_env import authenticate
from google_sheets import get_next_customer_number, increment_customer_number
from google_drive import copy_shikin_plan
from chatwork_api import create_chatwork_group, debug_members_vs_contacts, resolve_admin_member_ids
import config

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hiramatsukenchiku-local-dev')

# アプリのパスワード（環境変数 APP_PASSWORD で上書き可能）
APP_PASSWORD = os.environ.get('APP_PASSWORD', 'hiramatsukenchiku')


@app.route('/')
def index():
    if not session.get('authenticated'):
        return render_template('login.html')
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    if password == APP_PASSWORD:
        session['authenticated'] = True
        return ('', 204)
    return ('パスワードが違います', 401)


@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')


@app.route('/api/chatwork-debug', methods=['GET'])
def chatwork_debug():
    """Chatwork APIトークン所有者と、config メンバーがコンタクトAPIに載るか確認"""
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': '認証が必要です'}), 401
    try:
        requested = config.CHATWORK_MEMBERS_ADMIN_BASE + config.CHATWORK_MEMBERS_PENDING_APPROVAL
        contact_info = debug_members_vs_contacts(requested)
        resolved = resolve_admin_member_ids(
            config.CHATWORK_MEMBERS_ADMIN_BASE,
            config.CHATWORK_MEMBERS_PENDING_APPROVAL
        )
        return jsonify({'success': True, **contact_info, **resolved})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/create', methods=['POST'])
def create_customer():
    if not session.get('authenticated'):
        return jsonify({'success': False, 'error': '認証が必要です'}), 401
    try:
        creds = authenticate()

        # ① 顧客番号を取得
        customer_no = get_next_customer_number(creds, config.MANAGEMENT_SPREADSHEET_ID)
        print(f"📋 顧客番号: {customer_no}")

        # ② 資金計画をコピー
        spreadsheet_url, spreadsheet_name = copy_shikin_plan(
            creds,
            config.SOURCE_SPREADSHEET_ID,
            customer_no,
            config.TARGET_FOLDER_ID
        )

        # ③ Chatworkグループを作成
        room_name = f"{customer_no}様【担当者名】①"
        description = (
            f"■ANDOAD顧客情報（施工管理リンク）\n\n"
            f"■お客様GoogleDriveリンク\n\n"
            f"■資金計画表\n{spreadsheet_url}\n\n"
            f"■議事録（NotebookLM）"
        )
        room_id, room_url, added_members, skipped_members = create_chatwork_group(
            room_name,
            description,
            config.CHATWORK_MEMBERS_ADMIN_BASE,
            config.CHATWORK_MEMBERS_PENDING_APPROVAL
        )

        # ④ 顧客番号を+1して保存
        increment_customer_number(creds, config.MANAGEMENT_SPREADSHEET_ID)

        return jsonify({
            'success': True,
            'customer_no': customer_no,
            'spreadsheet_name': spreadsheet_name,
            'spreadsheet_url': spreadsheet_url,
            'chatwork_room_name': room_name,
            'chatwork_room_url': room_url,
            'added_members': added_members,
            'skipped_members': skipped_members,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5050)
