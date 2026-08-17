# =========================
# 第一阶段：构建 Vue 前端
# =========================
FROM node:22-alpine AS build

WORKDIR /app

# 先复制依赖定义文件，充分利用 Docker 缓存。
COPY package.json package-lock.json ./

# 严格按照 package-lock.json 安装依赖。
RUN npm ci

# 复制前端源码。
COPY . .

# 使用 production 模式构建。
RUN npm run build


# =========================
# 第二阶段：Nginx 提供静态文件
# =========================
FROM nginx:alpine

# 替换默认 Nginx 配置。
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制 Vue 构建产物。
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80