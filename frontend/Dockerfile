FROM node:22-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./

# 腾讯云服务器使用腾讯云 NPM 镜像
RUN npm ci --registry=https://mirrors.cloud.tencent.com/npm/

COPY . .

RUN npm run build-only


FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80