<template>
  <div class="app-layout">
    <!-- 左侧导航 -->
    <aside class="sidebar">
      <!-- Logo / 名称 -->
      <div class="sidebar-header">
        <div class="logo">D</div>

        <span class="app-name"> Desktop Tool </span>
      </div>

      <!-- 主菜单 -->
      <el-menu class="sidebar-menu" :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon> <HomeFilled /> </el-icon>
          <span>首页</span>
        </el-menu-item>

        <el-menu-item index="/tool">
          <el-icon> <Tools /> </el-icon>
          <span>工具</span>
        </el-menu-item>
      </el-menu>

      <div class="sidebar-footer">
        <el-menu :default-active="activeMenu" router>
          <el-menu-item index="/settings">
            <el-icon> <Setting /> </el-icon>
            <span>设置</span>
          </el-menu-item>
        </el-menu>
      </div>
    </aside>

    <!-- 右侧内容 -->
    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { HomeFilled, Tools, Setting } from '@element-plus/icons-vue'

const route = useRoute()

const activeMenu = computed(() => route.path)
</script>

<style scoped>
.app-layout {
  display: flex;

  width: 100vw;
  height: 100vh;

  overflow: hidden;

  background: #f5f6f8;
}

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

.sidebar-menu {
  flex: 1;

  min-height: 0;

  border-right: none;
}

.main-content {
  flex: 1;

  min-width: 0;
  min-height: 0;

  overflow: auto;

  padding: 24px;

  box-sizing: border-box;
}
</style>
