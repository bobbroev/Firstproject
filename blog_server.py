from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import mysql.connector
import hashlib
import os
from urllib.parse import parse_qs, urlparse
import uuid

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'admin',
    'password': 'y88888',
    'database': 'blog_db'
}

# 用于存储用户会话信息的字典
sessions = {}

def get_db():
    """创建并返回数据库连接"""
    return mysql.connector.connect(**db_config)

def generate_salt():
    """生成随机盐值用于密码加密"""
    return os.urandom(16).hex()

def hash_password(password, salt):
    """使用MD5和盐值对密码进行加密"""
    return hashlib.md5((password + salt).encode()).hexdigest()

class BlogHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        url = urlparse(self.path)
        
        if url.path == '/':
            # 提供主页
            self.serve_file('templates/index.html', 'text/html')
        elif url.path.startswith('/static/'):
            # 提供静态文件（CSS、JS等）
            file_path = url.path[1:]  # 移除开头的/
            if file_path.endswith('.css'):
                self.serve_file(file_path, 'text/css')
            elif file_path.endswith('.js'):
                self.serve_file(file_path, 'text/javascript')
        elif url.path == '/api/posts':
            # 获取文章列表
            self.handle_get_posts()
        else:
            self.send_error(404)

    def do_POST(self):
        """处理POST请求"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        if self.path == '/api/register':
            # 处理用户注册
            self.handle_register(data)
        elif self.path == '/api/login':
            # 处理用户登录
            self.handle_login(data)
        elif self.path == '/api/posts':
            # 处理创建新文章
            self.handle_create_post(data)
        else:
            self.send_error(404)

    def do_PUT(self):
        """处理PUT请求（更新文章）"""
        if self.path.startswith('/api/posts/'):
            post_id = int(self.path.split('/')[-1])
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            self.handle_update_post(post_id, data)
        else:
            self.send_error(404)

    def do_DELETE(self):
        """处理DELETE请求（删除文章）"""
        if self.path.startswith('/api/posts/'):
            post_id = int(self.path.split('/')[-1])
            self.handle_delete_post(post_id)
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检请求）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def serve_file(self, filename, content_type):
        """提供静态文件服务"""
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            self.send_response(200)
            if content_type.startswith('text/'):
                content_type += '; charset=utf-8'
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def send_json_response(self, data):
        """发送 JSON 响应"""
        self.send_response(200)  # HTTP 状态码
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')  # CORS 设置
        self.end_headers()
        # 将 Python 对象转换为 JSON 字符串并发送
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def get_session(self):
        """获取当前用户的会话信息"""
        cookie = self.headers.get('Cookie')
        if cookie:
            for item in cookie.split(';'):
                if item.strip().startswith('session='):
                    session_id = item.split('=')[1].strip()
                    return sessions.get(session_id)
        return None

    def handle_register(self, data):
        """处理用户注册"""
        username = data['username']
        password = data['password']
        
        # 生成盐值和加密密码
        salt = generate_salt()
        hashed_password = hash_password(password, salt)
        
        db = get_db()
        cursor = db.cursor()
        
        try:
            # 插入新用户记录
            cursor.execute("INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)",
                         (username, hashed_password, salt))
            db.commit()
            self.send_json_response({'status': 'success'})
        except:
            self.send_json_response({'status': 'error', 'message': '用户名已存在'})
        finally:
            cursor.close()
            db.close()

    def handle_login(self, data):
        """处理登录请求"""
        username = data['username']
        password = data['password']
        
        # 3. 与数据库交互
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, password, salt FROM users WHERE username = %s", 
                      (username,))
        
        # 4. 发送响应给前端
        self.send_json_response({'status': 'success'})

    def handle_get_posts(self):
        """获取文章列表"""
        db = get_db()
        cursor = db.cursor(dictionary=True)  # 返回字典格式的结果
        
        # 执行 SQL 查询
        cursor.execute("""
            SELECT 
                posts.id,
                posts.title,
                posts.content,
                posts.created_at,
                users.username 
            FROM posts 
            JOIN users ON posts.user_id = users.id 
            ORDER BY created_at DESC
        """)
        
        # 获取查询结果
        posts = cursor.fetchall()

    def handle_create_post(self, data):
        """创建新文章"""
        session = self.get_session()
        if not session:
            self.send_json_response({'status': 'error', 'message': '未登录'})
            return

        db = get_db()
        cursor = db.cursor()
        # 插入新文章
        cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (%s, %s, %s)",
                      (session['user_id'], data['title'], data['content']))
        db.commit()
        self.send_json_response({'status': 'success'})

    def handle_update_post(self, post_id, data):
        """更新文章"""
        session = self.get_session()
        if not session:
            self.send_json_response({'status': 'error', 'message': '未登录'})
            return

        db = get_db()
        cursor = db.cursor()
        
        # 检查文章所有权
        cursor.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        
        if not post or post[0] != session['user_id']:
            self.send_json_response({'status': 'error', 'message': '无权限'})
            return

        # 更新文章内容
        cursor.execute("UPDATE posts SET title = %s, content = %s WHERE id = %s",
                      (data['title'], data['content'], post_id))
        db.commit()
        self.send_json_response({'status': 'success'})

    def handle_delete_post(self, post_id):
        """删除文章"""
        session = self.get_session()
        if not session:
            self.send_json_response({'status': 'error', 'message': '未登录'})
            return

        db = get_db()
        cursor = db.cursor()
        
        # 检查文章所有权
        cursor.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        
        if not post or post[0] != session['user_id']:
            self.send_json_response({'status': 'error', 'message': '无权限'})
            return

        # 删除文章
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        db.commit()
        self.send_json_response({'status': 'success'})

def run(server_class=HTTPServer, handler_class=BlogHandler, port=8000):
    """启动HTTP服务器"""
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run() 