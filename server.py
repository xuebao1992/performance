#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雪豹市场部绩效考核工作台 - 后端服务
数据存储在飞书多维表格中
"""
import os
import json
import time
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='static', static_url_path='')

# ============ 配置 ============
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', 'cli_aa23415d8c781bb7')
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', 'w4NtPJV1MuJkdTqDoWiMBcpSLgqkFth1')
BITABLE_APP_TOKEN = os.environ.get('BITABLE_APP_TOKEN', 'SUCswFlF5i3zwxkrHADci1Emnl3')
BITABLE_TABLE_ID = os.environ.get('BITABLE_TABLE_ID', 'tblUq5sXETfPDOwH')
ACCESS_PASSWORD = os.environ.get('ACCESS_PASSWORD', 'xuebao2026')

# ============ 飞书API ============
_token_cache = {'token': None, 'expire_at': 0}

def get_tenant_token():
    """获取飞书tenant_access_token，带缓存"""
    now = time.time()
    if _token_cache['token'] and now < _token_cache['expire_at'] - 60:
        return _token_cache['token']
    
    url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
    data = json.dumps({
        'app_id': FEISHU_APP_ID,
        'app_secret': FEISHU_APP_SECRET
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode('utf-8'))
    if result.get('code') == 0:
        _token_cache['token'] = result['tenant_access_token']
        _token_cache['expire_at'] = now + result.get('expire', 7200)
        return _token_cache['token']
    raise Exception(f'获取飞书token失败: {result}')

def feishu_api(method, path, body=None):
    """调用飞书API"""
    token = get_tenant_token()
    url = f'https://open.feishu.cn/open-apis{path}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))

def ensure_fields():
    """确保多维表格有需要的字段"""
    result = feishu_api('GET', f'/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/fields')
    existing = {f['field_name'] for f in result.get('data', {}).get('items', [])}
    
    needed = [
        ('record_key', 1),   # 文本：month_emp_id
        ('emp_name', 1),     # 文本：员工姓名
        ('score_data', 1),   # 文本：评分JSON
    ]
    
    for name, ftype in needed:
        if name not in existing:
            feishu_api('POST', f'/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/fields', {
                'field_name': name,
                'type': ftype
            })
            print(f'创建字段: {name}')

# 启动时确保字段存在
try:
    ensure_fields()
except Exception as e:
    print(f'字段检查失败: {e}')

# ============ 数据操作 ============
def find_record(record_key):
    """根据record_key查找记录"""
    result = feishu_api('POST', f'/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/search', {
        'filter': {
            'conjunction': 'and',
            'conditions': [
                {'field_name': 'record_key', 'operator': 'is', 'value': [record_key]}
            ]
        }
    })
    items = result.get('data', {}).get('items', [])
    return items[0] if items else None

def get_score(month, emp_id):
    """获取某个员工某月的评分"""
    record_key = f'{month}_{emp_id}'
    record = find_record(record_key)
    if record:
        fields = record.get('fields', {})
        score_data = fields.get('score_data', '')
        if isinstance(score_data, list):  # 飞书富文本
            score_data = ''.join([t.get('text', '') for t in score_data])
        try:
            return json.loads(score_data) if score_data else {}
        except:
            return {}
    return {}

def save_score(month, emp_id, emp_name, score_data):
    """保存某个员工某月的评分"""
    record_key = f'{month}_{emp_id}'
    fields = {
        'record_key': record_key,
        'emp_name': emp_name,
        'score_data': json.dumps(score_data, ensure_ascii=False)
    }
    
    record = find_record(record_key)
    if record:
        # 更新
        record_id = record['record_id']
        result = feishu_api('PUT', f'/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/{record_id}', {
            'fields': fields
        })
    else:
        # 新建
        result = feishu_api('POST', f'/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records', {
            'fields': fields
        })
    return result.get('code') == 0

def get_all_scores(month):
    """获取某月所有员工的评分"""
    result = feishu_api('POST', f'/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records/search', {
        'filter': {
            'conjunction': 'and',
            'conditions': [
                {'field_name': 'record_key', 'operator': 'contains', 'value': [month + '_']}
            ]
        },
        'page_size': 100
    })
    scores = {}
    for item in result.get('data', {}).get('items', []):
        fields = item.get('fields', {})
        key = fields.get('record_key', '')
        if isinstance(key, list):
            key = ''.join([t.get('text', '') for t in key])
        emp_id = key.replace(month + '_', '')
        score_data = fields.get('score_data', '')
        if isinstance(score_data, list):
            score_data = ''.join([t.get('text', '') for t in score_data])
        try:
            scores[emp_id] = json.loads(score_data) if score_data else {}
        except:
            scores[emp_id] = {}
    return scores

# ============ API路由 ============
@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'time': time.time()})

@app.route('/api/score', methods=['GET'])
def api_get_score():
    month = request.args.get('month', '')
    emp_id = request.args.get('emp_id', '')
    if not month or not emp_id:
        return jsonify({'error': '缺少参数'}), 400
    score = get_score(month, emp_id)
    return jsonify({'month': month, 'emp_id': emp_id, 'score': score})

@app.route('/api/score', methods=['POST'])
def api_save_score():
    body = request.get_json()
    month = body.get('month', '')
    emp_id = body.get('emp_id', '')
    emp_name = body.get('emp_name', '')
    score = body.get('score', {})
    if not month or not emp_id:
        return jsonify({'error': '缺少参数'}), 400
    success = save_score(month, emp_id, emp_name, score)
    return jsonify({'success': success})

@app.route('/api/scores', methods=['GET'])
def api_get_scores():
    month = request.args.get('month', '')
    if not month:
        return jsonify({'error': '缺少参数'}), 400
    scores = get_all_scores(month)
    return jsonify({'month': month, 'scores': scores})

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
