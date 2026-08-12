<template>
  <div class="app-layout">
    <!-- 左侧导航 -->
    <aside class="sidebar">
      <!-- Logo / 名称 -->
      <div class="sidebar-header">
        <div class="logo">D</div>

        <span class="app-name">Rating System</span>
      </div>

      <!-- 主菜单 -->
      <el-menu class="sidebar-menu" :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>

        <el-menu-item index="/ratingItem">
          <el-icon><Files /></el-icon>
          <span>评分项目</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-menu :default-active="activeMenu" router>
          <el-menu-item index="/setting">
            <el-icon><Setting /></el-icon>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </div>
    </aside>

    <!-- 右侧区域 -->
    <div class="main-area">
      <!-- 顶部导航页头 -->
      <header class="main-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>

        <div class="header-right">
          <!-- 后面可以放用户信息、按钮等 -->
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="main-content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, Files, Setting } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)

const pageTitle = computed(() => {
  return route.meta.title as string
})
</script>

<style scoped>
.app-layout {
  display: flex;

  width: 100%;
  height: 100%;

  overflow: hidden;

  background: #f5f6f8;
}

/* ====================
   左侧导航
==================== */

.sidebar {
  width: 220px;
  height: 100%;

  flex-shrink: 0;

  display: flex;
  flex-direction: column;

  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}

.sidebar-header {
  height: 64px;
  padding: 0 20px;

  flex-shrink: 0;

  display: flex;
  align-items: center;

  box-sizing: border-box;
}

.logo {
  width: 32px;
  height: 32px;

  flex-shrink: 0;

  display: flex;
  align-items: center;
  justify-content: center;

  border-radius: 8px;

  background: #409eff;

  color: white;

  font-size: 16px;
  font-weight: 600;
}

.app-name {
  margin-left: 10px;

  font-size: 16px;
  font-weight: 600;

  color: #303133;
}

.sidebar-menu {
  flex: 1;

  min-height: 0;

  border-right: none;
}

.sidebar-footer {
  flex-shrink: 0;

  border-top: 1px solid #e5e7eb;
}

.sidebar-footer :deep(.el-menu) {
  border-right: none;
}

/* ====================
   右侧整体区域
==================== */

.main-area {
  flex: 1;

  min-width: 0;
  min-height: 0;

  display: flex;
  flex-direction: column;

  overflow: hidden;
}

/* ====================
   顶部页头
==================== */

.main-header {
  height: 64px;

  flex-shrink: 0;

  padding: 0 24px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  box-sizing: border-box;

  background: #ffffff;

  border-bottom: 1px solid #e5e7eb;
}

.header-left {
  display: flex;
  align-items: center;
}

.page-title {
  font-size: 18px;
  font-weight: 600;

  color: #303133;
}

.header-right {
  display: flex;
  align-items: center;

  gap: 12px;
}

/* ====================
   页面内容
==================== */

.main-content {
  flex: 1;

  min-width: 0;
  min-height: 0;

  overflow: auto;

  padding: 24px;

  box-sizing: border-box;
}
</style>
