# Nginx 配置完成文档

## 任务概述

**任务 ID:** 36.2 配置 Nginx  
**完成时间:** 2025年  
**状态:** ✅ 已完成

## 实现内容

本任务完成了合同预审看板系统的 Nginx 反向代理配置,包括:

### 1. Nginx 配置文件

创建了两个 Nginx 配置文件,分别用于开发和生产环境:

#### `nginx/nginx.conf` - 开发环境配置

**功能特性:**
- ✅ 反向代理到 Vite 开发服务器 (端口 5173)
- ✅ 支持 Vite HMR (热模块替换)
- ✅ 代理后端 API 请求 (端口 8000)
- ✅ WebSocket 代理支持 (Socket.IO)
- ✅ Gzip 压缩
- ✅ 文件上传限制 (20MB)

**路由配置:**
```
/ → frontend:5173 (Vite 开发服务器)
/api/* → backend:8000 (后端 API)
/socket.io/* → backend:8000 (WebSocket)
/health → backend:8000/health (健康检查)
```

#### `nginx/nginx.prod.conf` - 生产环境配置

**功能特性:**
- ✅ 直接服务前端构建产物 (静态文件)
- ✅ 静态资源缓存优化 (JS/CSS/图片缓存 1 年)
- ✅ HTML 文件不缓存 (支持即时更新)
- ✅ 安全响应头 (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)
- ✅ SPA 路由支持 (try_files)
- ✅ 隐藏 Nginx 版本号
- ✅ 禁止访问隐藏文件和备份文件

**路由配置:**
```
/ → /usr/share/nginx/html (静态文件)
/api/* → backend:8000 (后端 API)
/socket.io/* → backend:8000 (WebSocket)
/health → backend:8000/health (健康检查)
```

### 2. Docker 配置

#### `nginx/Dockerfile` - 开发环境镜像

```dockerfile
FROM nginx:1.25-alpine
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
HEALTHCHECK --interval=30s CMD wget --spider http://localhost/health
```

#### `nginx/Dockerfile.prod` - 生产环境镜像

```dockerfile
FROM nginx:1.25-alpine
COPY nginx.prod.conf /etc/nginx/nginx.conf
COPY ../frontend/dist /usr/share/nginx/html
EXPOSE 80
```

### 3. Docker Compose 配置

#### `docker-compose.dev.yml` - 开发环境

新增 Nginx 服务配置:

```yaml
nginx:
  build:
    context: ./nginx
    dockerfile: Dockerfile
  container_name: contract_review_nginx
  ports:
    - "80:80"
  depends_on:
    - backend
    - frontend
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - nginx_logs:/var/log/nginx
  networks:
    - contract_review_network
  restart: unless-stopped
```

### 4. 启动脚本

#### `start-with-nginx.sh` - 一键启动脚本

提供三种启动模式:

1. **开发模式** - 使用 docker-compose.dev.yml
   - 启动所有服务 (包括 Nginx)
   - 支持热重载
   - 适合本地开发

2. **生产模式** - 使用 docker-compose.yml
   - 完整 Docker 部署
   - 自动构建前端
   - 适合生产环境

3. **混合模式** - 基础服务 + Nginx
   - Docker 运行基础服务和 Nginx
   - 手动运行前后端
   - 灵活调试

### 5. 文档

#### `nginx/README.md` - 详细使用文档

包含以下内容:
- ✅ 文件说明
- ✅ 使用方法 (开发/生产)
- ✅ 路由配置
- ✅ 性能优化
- ✅ WebSocket 配置
- ✅ 安全配置
- ✅ 日志管理
- ✅ 健康检查
- ✅ 故障排查
- ✅ 配置修改指南
- ✅ 性能调优建议

## 技术实现细节

### 1. 反向代理配置

**前端代理 (开发环境):**
```nginx
location / {
    proxy_pass http://frontend:5173;
    proxy_http_version 1.1;
    
    # Vite HMR 支持
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

**后端 API 代理:**
```nginx
location /api/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    
    # 超时设置 (AI 请求可能较慢)
    proxy_read_timeout 120s;
    
    # 禁用缓冲 (流式响应)
    proxy_buffering off;
}
```

### 2. WebSocket 代理

**Socket.IO 配置:**
```nginx
location /socket.io/ {
    proxy_pass http://backend:8000;
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

### 3. 性能优化

**Gzip 压缩:**
```nginx
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css text/javascript application/json;
```

**静态资源缓存 (生产环境):**
```nginx
# JS/CSS/图片 - 强缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# HTML - 不缓存
location ~* \.html$ {
    expires -1;
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}
```

**连接优化:**
```nginx
upstream backend {
    server backend:8000;
    keepalive 64;  # 连接池
}
```

### 4. 安全配置

**安全响应头 (生产环境):**
```nginx
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
server_tokens off;  # 隐藏版本号
```

**文件上传限制:**
```nginx
client_max_body_size 20M;
```

**禁止访问敏感文件:**
```nginx
location ~ /\. {
    deny all;
}
```

### 5. 健康检查

**Docker 健康检查:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health
```

## 使用方法

### 快速启动

```bash
# 方式 1: 使用一键启动脚本
./start-with-nginx.sh

# 方式 2: 使用 docker-compose (开发)
docker-compose -f docker-compose.dev.yml up -d

# 方式 3: 使用 docker-compose (生产)
docker-compose up -d
```

### 访问地址

**开发环境:**
- 应用入口 (Nginx): http://localhost
- 前端 (Vite): http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/api/docs

**生产环境:**
- 应用入口: http://localhost
- API 文档: http://localhost:8000/api/docs

### 查看日志

```bash
# Nginx 日志
docker logs -f contract_review_nginx

# 访问日志
docker exec contract_review_nginx tail -f /var/log/nginx/access.log

# 错误日志
docker exec contract_review_nginx tail -f /var/log/nginx/error.log
```

### 重载配置

```bash
# 测试配置
docker exec contract_review_nginx nginx -t

# 重载配置 (不中断服务)
docker exec contract_review_nginx nginx -s reload
```

## 验证测试

### 1. 基本功能测试

```bash
# 测试健康检查
curl http://localhost/health

# 测试前端访问
curl -I http://localhost/

# 测试 API 访问
curl http://localhost/api/health

# 测试 WebSocket (使用浏览器开发者工具)
# 打开 http://localhost 查看 Network -> WS
```

### 2. 性能测试

```bash
# 测试 Gzip 压缩
curl -H "Accept-Encoding: gzip" -I http://localhost/

# 测试缓存头
curl -I http://localhost/assets/index.js

# 测试并发连接
ab -n 1000 -c 100 http://localhost/
```

### 3. 安全测试

```bash
# 测试隐藏文件访问
curl -I http://localhost/.env

# 测试安全响应头
curl -I http://localhost/ | grep -E "X-Content-Type-Options|X-Frame-Options"

# 测试文件上传限制
curl -X POST -F "file=@large_file.pdf" http://localhost/api/upload
```

## 目录结构

```
project/
├── nginx/
│   ├── Dockerfile              # 开发环境镜像
│   ├── Dockerfile.prod         # 生产环境镜像
│   ├── nginx.conf              # 开发环境配置
│   ├── nginx.prod.conf         # 生产环境配置
│   └── README.md               # 详细文档
├── docker-compose.yml          # 生产环境 compose
├── docker-compose.dev.yml      # 开发环境 compose (新增)
├── start-with-nginx.sh         # 一键启动脚本 (新增)
└── NGINX_SETUP.md              # 本文档
```

## 与设计文档的对应关系

根据 `design.md` 的要求,本实现完成了以下内容:

### 系统架构 - 部署层

✅ **Nginx - 反向代理和静态资源服务**
- 实现了反向代理功能
- 实现了静态资源服务
- 实现了 WebSocket 代理
- 实现了负载均衡准备 (upstream 配置)

### 通信机制

✅ **HTTP REST API**
- 通过 Nginx 代理到后端 (端口 8000)
- 路径: `/api/*`

✅ **WebSocket (Socket.io)**
- 通过 Nginx 代理 WebSocket 连接
- 路径: `/socket.io/*`
- 支持长连接 (7 天超时)

### 性能优化策略

✅ **前端优化**
- 静态资源缓存 (1 年)
- Gzip 压缩
- CDN 准备 (缓存头配置)

✅ **后端优化**
- 连接池 (keepalive)
- 请求缓冲优化
- 超时配置优化

### 部署配置

✅ **Docker + Docker Compose - 容器化部署**
- 创建了 Nginx Docker 镜像
- 集成到 docker-compose 配置
- 支持开发和生产环境

✅ **Nginx - 反向代理和静态资源服务**
- 完整的 Nginx 配置
- 开发和生产环境分离
- 安全和性能优化

## 需求覆盖

本实现覆盖了以下需求:

- ✅ **需求 10.1-10.10** - 用户界面交互 (通过 Nginx 提供前端服务)
- ✅ **需求 12.1-12.7** - 响应式布局 (Nginx 服务前端应用)
- ✅ **需求 8.8** - 部署配置 (Docker + Nginx)

## 后续优化建议

### 1. HTTPS 支持

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    # ... 其他配置
}
```

### 2. 负载均衡

```nginx
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
    keepalive 64;
}
```

### 3. 限流配置

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

location /api/ {
    limit_req zone=api burst=20;
    # ... 其他配置
}
```

### 4. 访问控制

```nginx
# IP 白名单
location /api/admin/ {
    allow 192.168.1.0/24;
    deny all;
    # ... 其他配置
}
```

### 5. 日志分析

集成日志分析工具:
- ELK Stack (Elasticsearch + Logstash + Kibana)
- Grafana + Loki
- GoAccess (实时日志分析)

## 总结

本任务成功完成了 Nginx 反向代理的配置,实现了:

1. ✅ 完整的开发和生产环境配置
2. ✅ WebSocket 代理支持
3. ✅ 性能优化 (压缩、缓存、连接池)
4. ✅ 安全配置 (响应头、文件限制)
5. ✅ Docker 集成
6. ✅ 详细的文档和使用指南
7. ✅ 一键启动脚本

系统现在可以通过 Nginx 统一入口访问,提供了更好的性能、安全性和可维护性。

## 相关文件

- `nginx/nginx.conf` - 开发环境配置
- `nginx/nginx.prod.conf` - 生产环境配置
- `nginx/Dockerfile` - 开发环境镜像
- `nginx/Dockerfile.prod` - 生产环境镜像
- `nginx/README.md` - 详细使用文档
- `docker-compose.dev.yml` - 开发环境 compose
- `start-with-nginx.sh` - 一键启动脚本
- `NGINX_SETUP.md` - 本文档
