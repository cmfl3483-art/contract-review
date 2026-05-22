# Nginx Dockerfile - 合同预审看板系统
# Contract Pre-Review System - Nginx Docker Image

FROM nginx:1.25-alpine

# 维护者信息
LABEL maintainer="Contract Pre-Review System"
LABEL description="Nginx reverse proxy for Contract Pre-Review System"

# 删除默认配置
RUN rm /etc/nginx/nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# 复制 Nginx 配置文件
# 开发环境使用 nginx.conf
# 生产环境使用 nginx.prod.conf
COPY nginx.conf /etc/nginx/nginx.conf

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
