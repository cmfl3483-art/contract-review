# Nginx 配置说明

## 概述

本目录包含合同预审看板系统的 Nginx 反向代理配置。Nginx 作为系统的入口,负责:

- 反向代理前端和后端服务
- WebSocket 连接代理 (Socket.IO)
- 静态资源服务和缓存
- 负载均衡和性能优化
- 安全防护

## 文件说明

### 配置文件

- **nginx.conf** - 开发环境配置
  - 代理到 Vite 开发服务器 (端口 5173)
  - 支持 HMR (热模块替换)
  - 适合本地开发调试

- **nginx.prod.conf** - 生产环境配置
  - 直接服务前端构建产物 (静态文件)
  - 启用静态资源缓存
  - 添加安全响应头
  - 适合生产部署

### Docker 文件

- **Dockerfile** - 开发环境镜像
  - 使用 nginx.conf
  - 代理到开发服务器

- **Dockerfile.prod** - 生产环境镜像
  - 使用 nginx.prod.conf
  - 包含前端构建产物
  - 适合生产部署

## 使用方法

### 开发环境

#### 方式 1: 使用 docker-compose.dev.yml (推荐)

```bash
# 启动所有服务 (包括 Nginx)
docker-compose -f docker-compose.dev.yml up -d

# 访问应用
# 通过 Nginx: http://localhost
# 直接访问前端: http://localhost:5173
# 直接访问后端: http://localhost:8000
```

#### 方式 2: 本地运行前后端 + Docker Nginx

```bash
# 1. 启动基础服务 (PostgreSQL, Redis, MinIO)
docker-compose up -d postgres redis minio

# 2. 启动后端 (本地)
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 启动前端 (本地)
cd frontend
npm run dev

# 4. 启动 Nginx (Docker)
docker-compose -f docker-compose.dev.yml up -d nginx

# 访问应用: http://localhost
```

#### 方式 3: 完全本地运行 (不使用 Nginx)

```bash
# 使用项目根目录的启动脚本
./start-services.sh  # 启动 Docker 服务
./start-backend.sh   # 启动后端
./start-frontend.sh  # 启动前端

# 直接访问
# 前端: http://localhost:5173
# 后端: http://localhost:8000
```

### 生产环境

#### 构建生产镜像

```bash
# 1. 构建前端
cd frontend
npm run build

# 2. 构建 Nginx 生产镜像
cd ../nginx
docker build -f Dockerfile.prod -t contract-review-nginx:prod .

# 3. 运行生产容器
docker run -d \
  --name contract-review-nginx \
  -p 80:80 \
  --network contract_review_network \
  contract-review-nginx:prod
```

#### 使用 docker-compose (生产)

```bash
# 使用生产配置
docker-compose -f docker-compose.yml up -d

# 查看日志
docker-compose logs -f nginx
```

## 路由配置

### 开发环境路由

| 路径 | 目标 | 说明 |
|------|------|------|
| `/` | `frontend:5173` | 前端应用 (Vite 开发服务器) |
| `/api/*` | `backend:8000` | 后端 API |
| `/socket.io/*` | `backend:8000` | WebSocket 连接 |
| `/health` | `backend:8000/health` | 健康检查 |

### 生产环境路由

| 路径 | 目标 | 说明 |
|------|------|------|
| `/` | 静态文件 | 前端构建产物 |
| `/api/*` | `backend:8000` | 后端 API |
| `/socket.io/*` | `backend:8000` | WebSocket 连接 |
| `/health` | `backend:8000/health` | 健康检查 |

## 性能优化

### Gzip 压缩

- 启用 Gzip 压缩,压缩级别 6
- 压缩类型: HTML, CSS, JS, JSON, SVG, 字体文件
- 最小压缩大小: 1KB

### 静态资源缓存

**开发环境:**
- 不缓存,支持热更新

**生产环境:**
- JS/CSS/图片/字体: 缓存 1 年 (immutable)
- HTML: 不缓存 (no-store)
- 使用 `Cache-Control` 和 `Expires` 头

### 连接优化

- 启用 `keepalive` 连接复用
- 上游服务器连接池: 32-64 个连接
- TCP 优化: `tcp_nopush`, `tcp_nodelay`

## WebSocket 配置

Socket.IO 需要特殊的 WebSocket 配置:

```nginx
location /socket.io/ {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    
    # WebSocket 必需的头
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # 长连接超时 (7 天)
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
    
    # 禁用缓冲
    proxy_buffering off;
}
```

## 安全配置

### 生产环境安全头

```nginx
# 防止 MIME 类型嗅探
add_header X-Content-Type-Options nosniff;

# 防止点击劫持
add_header X-Frame-Options DENY;

# XSS 防护
add_header X-XSS-Protection "1; mode=block";

# 隐藏 Nginx 版本号
server_tokens off;
```

### 文件上传限制

```nginx
# 最大上传大小: 20MB
client_max_body_size 20M;
```

### 禁止访问隐藏文件

```nginx
location ~ /\. {
    deny all;
    access_log off;
    log_not_found off;
}
```

## 日志管理

### 日志位置

- 访问日志: `/var/log/nginx/access.log`
- 错误日志: `/var/log/nginx/error.log`

### 查看日志

```bash
# Docker 容器日志
docker logs -f contract_review_nginx

# 访问日志
docker exec contract_review_nginx tail -f /var/log/nginx/access.log

# 错误日志
docker exec contract_review_nginx tail -f /var/log/nginx/error.log
```

### 日志格式

```nginx
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for"';
```

## 健康检查

### Docker 健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1
```

### 手动检查

```bash
# 检查 Nginx 状态
docker exec contract_review_nginx nginx -t

# 检查健康端点
curl http://localhost/health

# 检查 Nginx 进程
docker exec contract_review_nginx ps aux | grep nginx
```

## 故障排查

### Nginx 无法启动

```bash
# 检查配置文件语法
docker exec contract_review_nginx nginx -t

# 查看错误日志
docker logs contract_review_nginx
```

### 502 Bad Gateway

可能原因:
1. 后端服务未启动
2. 后端服务端口错误
3. 网络配置问题

```bash
# 检查后端服务
docker ps | grep backend

# 检查网络连接
docker exec contract_review_nginx ping backend

# 查看 Nginx 错误日志
docker logs contract_review_nginx
```

### WebSocket 连接失败

可能原因:
1. WebSocket 代理配置错误
2. 超时设置过短
3. 防火墙阻止

```bash
# 检查 WebSocket 配置
docker exec contract_review_nginx cat /etc/nginx/nginx.conf | grep -A 10 "socket.io"

# 测试 WebSocket 连接
# 使用浏览器开发者工具查看 Network -> WS
```

### 静态资源 404

可能原因:
1. 前端未构建
2. 文件路径错误
3. 权限问题

```bash
# 检查静态文件
docker exec contract_review_nginx ls -la /usr/share/nginx/html

# 检查文件权限
docker exec contract_review_nginx ls -la /usr/share/nginx/html/index.html
```

## 配置修改

### 修改配置后重载

```bash
# 测试配置
docker exec contract_review_nginx nginx -t

# 重载配置 (不中断服务)
docker exec contract_review_nginx nginx -s reload

# 或重启容器
docker restart contract_review_nginx
```

### 修改端口

编辑 `docker-compose.dev.yml` 或 `docker-compose.yml`:

```yaml
nginx:
  ports:
    - "8080:80"  # 改为 8080 端口
```

### 添加 HTTPS

1. 准备 SSL 证书
2. 修改 Nginx 配置:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    # ... 其他配置
}

# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

3. 挂载证书:

```yaml
nginx:
  volumes:
    - ./ssl:/etc/nginx/ssl:ro
```

## 性能调优

### 工作进程数

```nginx
# 设置为 CPU 核心数
worker_processes auto;
```

### 连接数

```nginx
events {
    # 每个工作进程的最大连接数
    worker_connections 2048;
}
```

### 缓冲区大小

```nginx
client_body_buffer_size 128k;
client_max_body_size 20M;
```

## 参考资料

- [Nginx 官方文档](https://nginx.org/en/docs/)
- [Nginx 反向代理配置](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [WebSocket 代理配置](https://nginx.org/en/docs/http/websocket.html)
- [Socket.IO 文档](https://socket.io/docs/v4/)
