import json
import os

def load_config():
    """加载配置文件"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'configs',
        'config.json'
    )
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_progress(progress_data):
    """保存采集进度"""
    config = load_config()
    progress_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        config['storage']['progress_file']
    )
    with open(progress_path, 'w', encoding='utf-8') as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def load_progress():
    """加载采集进度"""
    config = load_config()
    progress_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        config['storage']['progress_file']
    )
    if os.path.exists(progress_path):
        with open(progress_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'sort_end': '', 'req_trace': ''}
