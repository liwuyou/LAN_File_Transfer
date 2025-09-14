from flask import Flask, send_from_directory, request, session, jsonify
import os
import json
import random
import time
from datetime import datetime

app = Flask(__name__, 
           static_folder='../frontend', 
           static_url_path='/static')
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# 数据目录配置
DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
USERS_DIR = os.path.join(DATA_DIR, 'users')
FILES_DIR = os.path.join(DATA_DIR, 'files')

# 确保目录存在
os.makedirs(USERS_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

# 消息目录
MESSAGES_DIR = os.path.join(DATA_DIR, 'messages')
os.makedirs(MESSAGES_DIR, exist_ok=True)

class UserManager:
    def __init__(self):
        self.users_dir = USERS_DIR
    
    def generate_user_id(self):
        """生成6位随机用户ID"""
        return random.randint(100000, 999999)
    
    def create_user(self, request):
        """创建新用户"""
        user_id = self.generate_user_id()
        
        # 确保ID唯一
        while os.path.exists(os.path.join(self.users_dir, f'{user_id}.json')):
            user_id = self.generate_user_id()
        
        user_data = {
            'user_id': user_id,
            'username': f'用户{user_id}',
            'avatar': 'default',
            'created_at': datetime.now().isoformat(),
            'last_seen': datetime.now().isoformat(),
            'ip_address': request.remote_addr or 'unknown'
        }
        
        # 保存用户数据
        user_file = os.path.join(self.users_dir, f'{user_id}.json')
        with open(user_file, 'w', encoding='utf-8') as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)
        
        return user_data
    
    def get_user(self, user_id):
        """获取用户信息"""
        user_file = os.path.join(self.users_dir, f'{user_id}.json')
        if os.path.exists(user_file):
            with open(user_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

# 创建用户管理器实例
user_manager = UserManager()

@app.before_request
def check_user_session():
    uid = session.get('user_id')
    if uid:
        user_file = os.path.join(USERS_DIR, f'{uid}.json')
        if os.path.exists(user_file):          # 文件在 → 正常
            return
        # 文件不在 → 尝试“复活”该 ID
        if _try_recover_user(uid, request):    # 重建成功
            return
        # 复活失败（ID 已被占用）→ 把会话清掉，重新注册
        session.clear()

    # 标准新用户流程
    user_data = user_manager.create_user(request)
    session.update(user_id  = user_data['user_id'],
                   username = user_data['username'],
                   avatar   = user_data['avatar'])
    print(f"注册新用户: {user_data['username']} (ID: {user_data['user_id']})")


def _try_recover_user(uid: int, request) -> bool:
    """
    试图用旧 uid 重建用户文件；若 uid 已被占用则返回 False
    """
    user_file = os.path.join(USERS_DIR, f'{uid}.json')
    if os.path.exists(user_file):          # 被别人占了
        return False

    user_data = {
        'user_id':   uid,
        'username':  f'用户{uid}',
        'avatar':    'default',
        'created_at': datetime.now().isoformat(),
        'last_seen': datetime.now().isoformat(),
        'ip_address': request.remote_addr or 'unknown'
    }
    with open(user_file, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)
    print(f"用户 {uid} 已复活")
    return True

def is_mobile_device(user_agent):
    """
    通过User-Agent判断是否为移动设备
    返回True表示移动设备，False表示PC设备
    """
    if not user_agent:
        return False
    
    user_agent = user_agent.lower()
    
    # 移动设备关键词
    mobile_keywords = [
        'iphone', 'ipod', 'ipad', 'android', 
        'blackberry', 'windows phone', 'mobile',
        'phone', 'tablet', 'kindle', 'silk',
        'opera mini', 'opera mobi', 'iemobile'
    ]
    
    # 检查是否包含移动设备关键词
    return any(keyword in user_agent for keyword in mobile_keywords)

@app.route('/api/user-info')
def get_user_info():
    """获取当前用户信息"""
    user_id = session.get('user_id')
    if user_id:
        user_data = user_manager.get_user(user_id)
        if user_data:
            return jsonify(user_data)
    return jsonify({'error': '用户未登录'}), 401

@app.route('/api/online-users')
def get_online_users():
    """获取所有在线用户信息"""
    online_users = []
    for user_file in os.listdir(USERS_DIR):
        if user_file.endswith('.json'):
            user_id = user_file.split('.')[0]
            try:
                user_data = user_manager.get_user(int(user_id))
                if user_data:
                    # 检查最后活跃时间（3分钟内活跃算在线）
                    last_seen = datetime.fromisoformat(user_data['last_seen'])
                    is_online = (datetime.now() - last_seen).total_seconds() < 180
                    user_data['is_online'] = is_online
                    online_users.append(user_data)
            except:
                continue
    return jsonify(online_users)

@app.route('/api/update-status', methods=['POST'])
def update_user_status():
    """更新用户最后活跃时间"""
    user_id = session.get('user_id')
    if user_id:
        user_file = os.path.join(USERS_DIR, f'{user_id}.json')
        if os.path.exists(user_file):
            with open(user_file, 'r+', encoding='utf-8') as f:
                user_data = json.load(f)
                user_data['last_seen'] = datetime.now().isoformat()
                f.seek(0)
                json.dump(user_data, f, ensure_ascii=False, indent=2)
                f.truncate()
            return jsonify({'success': True})
    return jsonify({'error': '更新失败'}), 400

def save_message(user_id, message_data):
    """保存消息到用户的消息文件"""
    try:
        messages_file = os.path.join(MESSAGES_DIR, f'{user_id}.json')
        
        messages = []
        if os.path.exists(messages_file):
            try:
                with open(messages_file, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
            except json.JSONDecodeError:
                messages = []
        
        messages.append(message_data)
        
        with open(messages_file, 'w', encoding='utf-8') as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        
        print(f" 消息保存成功 - 用户: {user_id}, 消息ID: {message_data['message_id']}")
        return True
    except Exception as e:
        print(f" 消息保存失败 - 用户: {user_id}, 错误: {e}")
        return False

def update_message_in_file(user_id, updated_message):
    """更新消息文件中的特定消息"""
    try:
        messages_file = os.path.join(MESSAGES_DIR, f'{user_id}.json')
        
        if not os.path.exists(messages_file):
            return False
        
        with open(messages_file, 'r+', encoding='utf-8') as f:
            messages = json.load(f)
            
            # 找到并更新对应的消息
            for i, msg in enumerate(messages):
                if msg['message_id'] == updated_message['message_id']:
                    messages[i] = updated_message
                    break
            
            f.seek(0)
            json.dump(messages, f, ensure_ascii=False, indent=2)
            f.truncate()
        
        print(f" 消息更新成功 - 用户: {user_id}, 消息ID: {updated_message['message_id']}")
        return True
    except Exception as e:
        print(f" 消息更新失败 - 用户: {user_id}, 错误: {e}")
        return False

def load_user_messages(user_id):
    """加载用户的所有消息"""
    messages_file = os.path.join(MESSAGES_DIR, f'{user_id}.json')
    if os.path.exists(messages_file):
        with open(messages_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """发送消息给指定用户"""
    data = request.json
    target_id = data.get('target_id')
    content = data.get('content')
    
    if not target_id or not content:
        return jsonify({'error': '缺少参数'}), 400
    
    # 验证目标用户存在
    target_user = user_manager.get_user(int(target_id))
    if not target_user:
        return jsonify({'error': '目标用户不存在'}), 404
    
    # 创建消息记录（确保时间戳唯一性）
    current_time = time.time_ns()  # 纳秒级时间戳确保唯一性
    message_data = {
        'message_id': f"msg_{current_time}",
        'sender_id': session['user_id'],
        'receiver_id': target_id,
        'type': 'text',
        'content': content,
        'timestamp': datetime.fromtimestamp(current_time / 1e9).isoformat(),
        'is_read': False,
        'is_polled': False  # 新增：是否已被轮询的标志位
    }
    
    # 保存消息到双方的消息记录
    save_message(session['user_id'], message_data)  # 发送方
    save_message(target_id, message_data)           # 接收方
    
    return jsonify({'success': True, 'message_id': message_data['message_id']})

@app.route('/api/messages/<target_id>')
def get_messages(target_id):
    """获取与指定用户的聊天记录"""
    user_id = session['user_id']
    messages = load_user_messages(user_id)
    
    # 过滤出与目标用户的对话
    conversation = [
        msg for msg in messages 
        if str(msg['sender_id']) == str(target_id) or str(msg['receiver_id']) == str(target_id)
    ]
    
    # 按时间排序
    conversation.sort(key=lambda x: x['timestamp'])
    
    return jsonify(conversation)

@app.route('/api/check-new-messages/<target_id>')
def check_new_messages(target_id):
    """检查是否有新消息（长轮询端点）"""
    user_id = session['user_id']
    messages = load_user_messages(user_id)
    
    # 获取最后一条消息的时间戳（如果有的话）
    last_timestamp = request.args.get('last_timestamp')
    
    print(f" 检查新消息 - 用户: {user_id}, 目标: {target_id}, 最后时间戳: {last_timestamp}")
    
    # 过滤出与目标用户的对话
    conversation = [
        msg for msg in messages 
        if str(msg['sender_id']) == str(target_id) or str(msg['receiver_id']) == str(target_id)
    ]
    
    # 查找未轮询的消息（来自目标用户）
    new_messages = [
        msg for msg in conversation 
        if str(msg['sender_id']) == str(target_id) and not msg.get('is_polled', False)
    ]
    
    # 标记这些消息为已轮询
    for msg in new_messages:
        msg['is_polled'] = True
        update_message_in_file(user_id, msg)
    
    print(f" 发现 {len(new_messages)} 条新消息")
    return jsonify(new_messages)

@app.route('/api/send-file', methods=['POST'])
def send_file():
    """上传并发送文件"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    target_id = request.form.get('target_id')
    
    if not target_id:
        return jsonify({'error': '缺少目标用户ID'}), 400
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 验证目标用户存在
    target_user = user_manager.get_user(int(target_id))
    if not target_user:
        return jsonify({'error': '目标用户不存在'}), 404
    
    # 创建用户文件目录
    user_files_dir = os.path.join(FILES_DIR, str(target_id))
    os.makedirs(user_files_dir, exist_ok=True)
    
    # 生成安全的文件名（时间戳+原始文件名）
    timestamp = int(time.time())
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(user_files_dir, safe_filename)
    
    # 保存文件
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    
    # 创建文件消息记录
    message_data = {
        'message_id': f"file_{int(time.time() * 1000)}",
        'sender_id': session['user_id'],
        'receiver_id': target_id,
        'type': 'file',
        'content': '文件消息',
        'file_info': {
            'original_name': file.filename,
            'saved_name': safe_filename,
            'size': file_size,
            'path': file_path,
            'upload_time': datetime.now().isoformat()
        },
        'timestamp': datetime.now().isoformat(),
        'is_read': False
    }
    
    # 保存消息到双方的消息记录
    save_message(session['user_id'], message_data)  # 发送方
    save_message(target_id, message_data)           # 接收方
    
    return jsonify({
        'success': True, 
        'message': message_data,
        'file_url': f'/api/download-file/{safe_filename}?user_id={target_id}'
    })

@app.route('/api/download-file/<filename>')
def download_file(filename):
    """下载文件"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': '缺少用户ID参数'}), 400
    
    # 验证文件属于该用户
    file_path = os.path.join(FILES_DIR, user_id, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在'}), 404
    
    # 检查文件访问权限（简化版，实际应该更严格的验证）
    if not filename.startswith(tuple(str(i) for i in range(10))):  # 简单的时间戳验证
        return jsonify({'error': '无效的文件名'}), 400
    
    return send_from_directory(os.path.dirname(file_path), 
                             os.path.basename(file_path), 
                             as_attachment=True)

@app.route('/')
def index():
    """
    根路由，根据设备类型自动跳转到对应页面
    """
    user_agent = request.headers.get('User-Agent', '')
    
    # 测试阶段，强制返回移动端页面
    return send_from_directory('../frontend/mobile', 'mobile_index.html')
    if is_mobile_device(user_agent):
        # 移动设备访问移动端页面
        return send_from_directory('../frontend/mobile', 'mobile_index.html')
    else:
        # PC设备访问PC端页面
        return send_from_directory('../frontend', 'pc_index.html')

if __name__ == '__main__':
    app.run(debug=True, port=8888, host='0.0.0.0')
