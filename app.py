from flask import Flask, render_template, jsonify, request
import pandas as pd
import json
import os

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# 加载配置
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    import yaml
    config = yaml.safe_load(f)

@app.route('/')
def device_list():
    # 传递设备列表到模板
    devices = config.get('devices', [])
    return render_template('device_list.html', devices=devices)

@app.route('/device/<device_id>')
def device_detail(device_id):
    # 查找设备信息
    device = next((d for d in config.get('devices', []) if d['id'] == device_id), None)
    if not device:
        return '设备不存在', 404
    return render_template('device_detail.html', device=device, device_id=device_id)

@app.route('/device/<device_id>/edit')
def device_edit(device_id):
    # 查找设备信息
    device = next((d for d in config.get('devices', []) if d['id'] == device_id), None)
    if not device:
        return '设备不存在', 404
    return render_template('device_edit.html', device=device, device_id=device_id)

@app.route('/device/<device_id>/history')
def device_history(device_id):
    # 查找设备信息
    device = next((d for d in config.get('devices', []) if d['id'] == device_id), None)
    if not device:
        return '设备不存在', 404
    return render_template('device_history.html', device=device, device_id=device_id)

@app.route('/device/<device_id>/alerts')
def device_alerts(device_id):
    # 查找设备信息
    device = next((d for d in config.get('devices', []) if d['id'] == device_id), None)
    if not device:
        return '设备不存在', 404
    return render_template('device_alerts.html', device=device, device_id=device_id)

@app.route('/api/data')
def get_data():
    # 获取设备ID参数，默认为第一个设备
    device_id = request.args.get('device_id', config['devices'][0]['id'] if config.get('devices') else 'device_1')
    
    # 加载原始数据
    raw_data_path = f"data/raw_data_{device_id}.csv"
    if not os.path.exists(raw_data_path):
        # 尝试另一种命名格式
        raw_data_path = f"data/raw_data_device_{device_id.split('_')[1]}.csv"
    
    if os.path.exists(raw_data_path):
        df = pd.read_csv(raw_data_path)
        if len(df) > 0:
            latest_data = df.tail(1).to_dict('records')[0]
        else:
            latest_data = {}
    else:
        latest_data = {}
    
    # 加载预警日志
    alert_log_path = f"logs/alert_log_{device_id}.csv"
    if not os.path.exists(alert_log_path):
        # 尝试另一种命名格式
        alert_log_path = f"logs/alert_log_device_{device_id.split('_')[1]}.csv"
    
    if os.path.exists(alert_log_path):
        alert_df = pd.read_csv(alert_log_path)
        if len(alert_df) > 0:
            latest_alert = alert_df.tail(1).to_dict('records')[0]
        else:
            latest_alert = {}
    else:
        latest_alert = {}
    
    return jsonify({
        'latest_data': latest_data,
        'latest_alert': latest_alert,
        'device_id': device_id
    })

@app.route('/api/history')
def get_history():
    # 获取设备ID参数，默认为第一个设备
    device_id = request.args.get('device_id', config['devices'][0]['id'] if config.get('devices') else 'device_1')
    
    # 获取时间范围参数
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    # 加载历史数据
    # 尝试多种文件路径格式
    raw_data_path = f"data/raw_data_{device_id}.csv"
    if not os.path.exists(raw_data_path):
        # 尝试另一种命名格式
        raw_data_path = f"data/raw_data_device_{device_id.split('_')[1]}.csv"
    
    if os.path.exists(raw_data_path):
        df = pd.read_csv(raw_data_path)
        
        # 处理时间筛选
        if start_time and end_time:
            try:
                # 先转换时间戳列
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # 转换时间格式
                start_time_obj = pd.to_datetime(start_time.replace('T', ' '))
                end_time_obj = pd.to_datetime(end_time.replace('T', ' '))
                
                # 筛选时间范围内的数据
                df = df[(df['timestamp'] >= start_time_obj) & (df['timestamp'] <= end_time_obj)]
                
                print(f"时间筛选: {start_time_obj} 到 {end_time_obj}")
                print(f"筛选后数据量: {len(df)}")
                print(f"筛选后时间范围: {df['timestamp'].min()} 到 {df['timestamp'].max()}")
            except Exception as e:
                print(f"时间筛选错误: {str(e)}")
        
        # 转换为字典格式
        history_data = {
            'timestamps': df['timestamp'].astype(str).tolist(),
            'pressure': df['pressure'].tolist(),
            'flow': df['flow'].tolist(),
            'valve_open': df['valve_open'].tolist(),
            'temperature': df['temperature'].tolist()
        }
    else:
        # 如果文件不存在，返回空数据
        history_data = {
            'timestamps': [],
            'pressure': [],
            'flow': [],
            'valve_open': [],
            'temperature': []
        }
    
    return jsonify(history_data)

@app.route('/api/alerts')
def get_alerts():
    # 获取设备ID参数，默认为第一个设备
    device_id = request.args.get('device_id', config['devices'][0]['id'] if config.get('devices') else 'device_1')
    
    # 加载预警日志
    alert_log_path = f"logs/alert_log_{device_id}.csv"
    if os.path.exists(alert_log_path):
        alert_df = pd.read_csv(alert_log_path)
        # 转换为字典格式
        alerts = alert_df.to_dict('records')
    else:
        alerts = []
    
    return jsonify(alerts)

@app.route('/api/set-mode', methods=['POST'])
def set_mode():
    # 获取请求参数
    data = request.json
    mode = data.get('mode')
    device_id = data.get('device_id', config['devices'][0]['id'] if config.get('devices') else 'device_1')
    
    # 调用模拟API设置模式
    import requests
    try:
        response = requests.post(f"http://localhost:8001/api/set-mode", params={'mode': mode, 'device_id': device_id})
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'设置模式失败: {str(e)}'})

@app.route('/api/update-device', methods=['POST'])
def update_device():
    # 获取请求参数
    data = request.json
    device_id = data.get('device_id')
    manager = data.get('manager')
    contact = data.get('contact')
    
    # 查找设备
    device = next((d for d in config.get('devices', []) if d['id'] == device_id), None)
    if not device:
        return jsonify({'success': False, 'message': '设备不存在'})
    
    # 更新设备信息
    device['manager'] = manager
    device['contact'] = contact
    
    # 保存到配置文件
    try:
        with open('config/config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        return jsonify({'success': True, 'message': '保存成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)