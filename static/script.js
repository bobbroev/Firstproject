document.addEventListener('DOMContentLoaded', function() {
    loadPosts();  // 页面加载完成后自动加载文章
});

let currentUser = null;

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    
    const response = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        currentUser = username;
        document.getElementById('auth-section').style.display = 'none';
        document.getElementById('post-section').style.display = 'block';
        loadPosts();
    } else {
        alert(data.message);
    }
}

async function register() {
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;
    
    const response = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        alert('注册成功，请登录');
    } else {
        alert(data.message);
    }
}

async function createPost() {
    const title = document.getElementById('post-title').value;
    const content = document.getElementById('post-content').value;
    
    const response = await fetch('/api/posts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ title, content })
    });
    
    const data = await response.json();
    if (data.status === 'success') {
        document.getElementById('post-title').value = '';
        document.getElementById('post-content').value = '';
        loadPosts();
    }
}

async function loadPosts() {
    try {
        // 1. 发送获取文章请求
        const response = await fetch('/api/posts');
        const data = await response.json();
        
        // 2. 处理响应数据
        if (data.status === 'error') {
            console.error("加载文章失败:", data.message);
            return;
        }
        
        // 3. 更新页面显示
        const posts = data.posts || [];
        const postsContainer = document.getElementById('posts-list');
        postsContainer.innerHTML = '';  // 清空现有内容
        
        posts.forEach(post => {
            // 创建文章 DOM 元素
            const postElement = document.createElement('div');
            postElement.className = 'post';
            postElement.innerHTML = `
                <h3>${post.title}</h3>
                <p>${post.content}</p>
            `;
            postsContainer.appendChild(postElement);
        });
    } catch (error) {
        console.error("加载文章时出错:", error);
    }
}

async function editPost(postId) {
    const newTitle = prompt('请输入新标题');
    const newContent = prompt('请输入新内容');
    
    if (newTitle && newContent) {
        const response = await fetch(`/api/posts/${postId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ title: newTitle, content: newContent })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            loadPosts();
        } else {
            alert(data.message);
        }
    }
}

async function deletePost(postId) {
    if (confirm('确定要删除这篇文章吗？')) {
        const response = await fetch(`/api/posts/${postId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            loadPosts();
        } else {
            alert(data.message);
        }
    }
} 