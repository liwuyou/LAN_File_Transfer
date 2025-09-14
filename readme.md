# LAN 文件传输系统

---

author：liwuyou
E-mail: liwuyou66@qq.com

---
一个基于Web的局域网文件传输系统，支持PC和移动端设备之间的文件传输和消息通信。

需要安装python3.7及以上版本
安装依赖库requirements.txt

开箱即用版本下载（不python，不装库，开箱即用）
https://wwqn.lanzoul.com/i1HNb366v30f

操作教程视频


## 🏗️ 项目结构

```
LAN_File_Transfer/
├── backend/                 # Python后端
│   ├── app.py              # Flask主应用
│   ├── tk_server_gui.py.py  # 启动主文件
│   ├── config.json          # 启动主文件配置文件 
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端文件
│   ├── pc_index.html       # PC端界面
│   ├── mobile/            # 移动端专用文件
│   │   ├── mobile_index.html
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   └── assets/
│   ├── css/               # 共享CSS
│   ├── js/                # 共享JavaScript
│   └── assets/            # 共享资源
└── data/                  # 数据存储
    ├── files/             # 上传的文件
    │   ├── {user_id}/     # 按用户ID分类
    │   └── ...
    ├── messages/          # 消息记录
    │   ├── {user_id}.json # 用户消息文件
    │   └── ...
    └── users/             # 用户信息
        ├── {user_id}.json # 用户配置文件
        └── ...
```

## 🎯 实现思路

### 后端架构 (Python Flask)

#### 核心功能：
1. **RESTful API** - 提供完整的API接口
2. **文件处理** - 支持大文件分块上传下载
3. **实时通信** - 基于轮询的消息系统
4. **用户管理** - 设备识别和状态维护

#### 关键技术：
- **Flask** - 轻量级Web框架
- **JSON存储** - 简单的文件数据库
- **CORS支持** - 跨域请求处理
- **文件流** - 高效的文件传输

### 前端架构

#### 双端设计：
1. **PC端** (`pc_index.html`)
   - 传统桌面界面布局
   - 适合鼠标操作
   - 大屏幕优化

2. **移动端** (`mobile/mobile_index.html`)
   - 响应式设计
   - 触摸交互优化
   - 移动端专属样式

#### 核心技术：
- **HTML5/CSS3** - 现代Web标准
- **Flex布局** - 灵活的页面布局
- **JavaScript ES6** - 现代JavaScript
- **Fetch API** - 异步数据请求

### 数据存储设计

#### 文件存储：
```json
// data/files/{user_id}/filename
{
  "original_name": "document.pdf",
  "saved_name": "timestamp_filename.ext",
  "size": 1024000,
  "upload_time": "2025-09-13T02:30:00"
}
```

#### 消息存储：
```json
// data/messages/{user_id}.json
[
  {
    "message_id": 1,
    "sender_id": 123,
    "receiver_id": 456,
    "type": "text",
    "content": "Hello!",
    "timestamp": "2025-09-13T02:30:00",
    "file_info": null
  }
]
```

#### 用户信息：
```json
// data/users/{user_id}.json
{
  "user_id": 123,
  "username": "User123",
  "device_type": "mobile",
  "last_online": "2025-09-13T02:30:00",
  "is_online": true
}
```

## 🔧 核心功能

### 1. 设备发现与连接
- 自动检测局域网内在线设备
- 心跳机制维护设备状态
- 实时更新用户列表

### 2. 文件传输
- 支持多文件同时上传
- 进度条显示传输状态
- 断点续传支持
- 文件类型识别和图标显示

### 3. 实时消息
- 文本消息即时通信
- 消息历史记录
- 自动滚动到最新消息
- 消息状态指示

### 4. 用户界面
- 响应式设计适配不同设备
- 直观的文件操作界面
- 清晰的用户状态显示
- 流畅的交互体验

## 🚀 启动方式

### 后端启动：
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 前端访问：
- PC端: `http://localhost:5000`
- 移动端: `http://localhost:5000/mobile`

## 🌟 技术特色

1. **零配置** - 自动发现局域网设备
2. **跨平台** - 支持任何现代浏览器
3. **无需安装** - 纯Web应用，无需客户端
4. **安全传输** - 局域网内直接传输
5. **实时更新** - 消息和状态实时同步

## 🔄 工作流程

1. **设备注册** - 用户访问页面时自动注册设备
2. **状态同步** - 定期心跳包更新在线状态
3. **消息轮询** - 定期检查新消息和文件
4. **文件传输** - 通过HTTP协议直接传输文件
5. **界面更新** - 根据设备类型加载相应界面

## 📊 性能优化

- **文件分块** - 大文件分块传输
- **缓存策略** - 合理的浏览器缓存
- **懒加载** - 按需加载资源
- **压缩传输** - Gzip压缩减小传输量

这个系统提供了一个简单而强大的局域网文件传输解决方案，适合家庭、办公室或教育环境使用。


---

本代码100%由AI生成，本人负责调教与思路及其debug，感谢deepseek.

---