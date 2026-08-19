<template>
  <div class="rating-item-page">
    <!-- 搜索区域 -->
    <section class="search-panel">
      <el-form :model="searchForm" inline class="search-form" @submit.prevent>
        <el-form-item label="评分主题">
          <el-select v-model="searchForm.topicId" placeholder="请选择评分主题" clearable filterable style="width: 220px">
            <el-option v-for="topic in topicList" :key="topic.id" :label="topic.name" :value="topic.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="项目名称">
          <el-input v-model="searchForm.name" placeholder="请输入项目名称" clearable style="width: 220px" @keyup.enter="handleSearch" />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable style="width: 160px">
            <el-option label="初始化" :value="0" />

            <el-option label="评分中" :value="1" />

            <el-option label="已评分" :value="2" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch"> 查询 </el-button>

          <el-button @click="handleReset"> 重置 </el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 表格区域 -->
    <section class="table-panel">
      <!-- 表格顶部工具栏 -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <span class="table-title"> 评分项目列表 </span>
        </div>

        <div class="toolbar-right">
          <el-button type="primary" @click="handleAdd">
            <el-icon>
              <Plus />
            </el-icon>

            新增评分项目
          </el-button>
        </div>
      </div>

      <!-- 表格 -->
      <el-table :data="tableData" v-loading="loading" border stripe style="width: 100%">
        <el-table-column type="index" label="序号" width="70" align="center" />

        <el-table-column label="所属主题" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">
            {{ getTopicName(row.topicId) }}
          </template>
        </el-table-column>

        <el-table-column prop="name" label="项目名称" min-width="150" show-overflow-tooltip />

        <el-table-column prop="description" label="项目描述" min-width="260" show-overflow-tooltip />

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">
              {{ statusMap[row.status]?.label ?? '未知状态' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right" align="center" class-name="operation-column">
          <template #default="{ row }">
            <el-button type="primary" :disabled="row.status !== 0" link @click="handleEdit(row)"> 编辑 </el-button>

            <el-button type="warning" link @click="handleRating(row)"> 评分 </el-button>

            <el-button type="danger" link @click="handleDelete(row)"> 删除 </el-button>
          </template>
        </el-table-column>

        <template #empty>
          <el-empty description="暂无评分项目" />
        </template>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </section>

    <AddOrUpdate v-model="dialogVisible" :item="currentItem" @success="handleAddOrUpdateSuccess" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { ElMessage, ElMessageBox } from 'element-plus'

import { Plus } from '@element-plus/icons-vue'

import { useRoute, useRouter } from 'vue-router'

import type { RatingItem, SearchForm, RatingTopic } from '@/types'

import { deleteRatingItem, getRatingItemList } from '@/api/rating/rating.ts'

import { queryRatingTopic } from '@/api/rating/RatingTopic.ts'

import AddOrUpdate from '@/views/rating/Item/AddOrUpdate.vue'

interface Pagination {
  page: number
  pageSize: number
  total: number
}

type StatusInfo = {
  label: string
  type: 'info' | 'warning' | 'success'
}

const statusMap: Record<number, StatusInfo> = {
  0: {
    label: '初始化',
    type: 'info',
  },

  1: {
    label: '评分中',
    type: 'warning',
  },

  2: {
    label: '已评分',
    type: 'success',
  },
}

const dialogVisible = ref(false)

const loading = ref(false)

const router = useRouter()
const route = useRoute()

/**
 * Topic 列表。
 *
 * 当前页面用于：
 * 1. Topic 搜索条件
 * 2. 根据 topicId 显示 Topic 名称
 */
const topicList = ref<RatingTopic[]>([])

const searchForm = reactive<SearchForm>({
  topicId: null,
  name: '',
  status: null,
})

const pagination = reactive<Pagination>({
  page: 1,
  pageSize: 10,
  total: 0,
})

const tableData = ref<RatingItem[]>([])

/**
 * 当前正在编辑的评分项目。
 *
 * null：
 *   表示新增模式。
 *
 * RatingItem：
 *   表示编辑模式。
 */
const currentItem = ref<RatingItem | null>(null)

/**
 * Topic ID -> Topic Name。
 *
 * 避免表格每一行反复遍历 topicList。
 */
const topicNameMap = computed(() => {
  return new Map(topicList.value.map((topic) => [topic.id, topic.name]))
})

/**
 * 查询 Topic 名称。
 */
function getTopicName(topicId: number | null): string {
  if (topicId == null) {
    return '--'
  }

  return topicNameMap.value.get(topicId) ?? `Topic #${topicId}`
}

/**
 * 从 URL query 中读取评分主题 ID。
 */
function loadTopicIdFromRoute() {
  const value = route.query.topicId

  if (typeof value !== 'string') {
    return
  }

  const topicId = Number(value)

  if (!Number.isInteger(topicId) || topicId <= 0) {
    return
  }

  searchForm.topicId = topicId
}

/**
 * 加载 Topic。
 *
 * 当前主要用于筛选和显示 Topic 名称。
 */
async function loadTopics() {
  const response = await queryRatingTopic({
    page: 1,
    pageSize: 100,
  })

  topicList.value = response.list
}

/**
 * 查询。
 */
function handleSearch() {
  pagination.page = 1

  loadData()
}

/**
 * 重置查询条件。
 */
async function handleReset() {
  searchForm.topicId = null
  searchForm.name = ''
  searchForm.status = null

  pagination.page = 1
  /**
   * 清除 URL 中从 Topic 页面带过来的筛选条件。
   */
  await router.replace({
    path: route.path,
    query: {},
  })
  await loadData()
}

/**
 * 加载 RatingItem。
 */
async function loadData() {
  loading.value = true

  try {
    const response = await getRatingItemList({
      topicId: searchForm.topicId ?? undefined,

      name: searchForm.name || undefined,

      // 注意：
      // status = 0 是合法值，
      // 不能使用 || undefined。
      status: searchForm.status ?? undefined,

      page: pagination.page,

      pageSize: pagination.pageSize,
    })

    tableData.value = response.list

    pagination.total = response.total
  } finally {
    loading.value = false
  }
}

/**
 * 打开新增弹窗。
 */
function handleAdd() {
  currentItem.value = null

  dialogVisible.value = true
}

/**
 * 打开编辑弹窗。
 */
function handleEdit(row: RatingItem) {
  currentItem.value = {
    ...row,
  }

  dialogVisible.value = true
}

/**
 * 跳转评分管理页面。
 */
function handleRating(row: RatingItem) {
  router.push({
    name: 'Rating',

    params: {
      id: row.id,
    },

    state: {
      item: {
        ...row,
      },
    },
  })
}

/**
 * 新增 / 修改成功后的统一处理。
 */
function handleAddOrUpdateSuccess(mode: 'add' | 'edit') {
  if (mode === 'add') {
    pagination.page = 1
  }

  loadData()
}

/**
 * 删除。
 */
async function handleDelete(row: RatingItem) {
  try {
    await ElMessageBox.confirm(`确认删除评分项目「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning' as const,
    })

    await deleteRatingItem(row.id)

    pagination.page = 1

    await loadData()

    ElMessage.success('删除成功')
  } catch {
    // 用户取消，不需要处理。
  }
}

/**
 * 修改每页数量。
 */
function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize
  pagination.page = 1

  loadData()
}

/**
 * 翻页。
 */
function handlePageChange(page: number) {
  pagination.page = page

  loadData()
}

onMounted(() => {
  loadTopicIdFromRoute()

  loadTopics()

  loadData()
})
</script>

<style scoped>
.rating-item-page {
  width: 100%;
  height: 100%;

  display: flex;
  flex-direction: column;

  gap: 16px;

  box-sizing: border-box;
}

/* =========================
   搜索区域
========================= */

.search-panel {
  flex-shrink: 0;

  padding: 20px 20px 2px;

  background: #ffffff;

  border: 1px solid #e5e7eb;
  border-radius: 8px;

  box-sizing: border-box;
}

.search-panel :deep(.el-form-item__label) {
  color: #606266;

  font-size: 14px;
}

.search-form {
  width: 100%;
}

/* =========================
   表格区域
========================= */

.table-panel {
  flex: 1;

  min-height: 0;

  display: flex;
  flex-direction: column;

  padding: 20px;

  background: #ffffff;

  border: 1px solid #e5e7eb;
  border-radius: 8px;

  box-sizing: border-box;
}

.table-toolbar {
  flex-shrink: 0;

  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 16px;
}

.table-title {
  color: #303133;

  font-size: 16px;
  font-weight: 600;
  line-height: 24px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
}

:deep(.operation-column) {
  border-left: 1px solid var(--el-table-border-color) !important;
}

/* =========================
   分页
========================= */

.pagination-wrapper {
  flex-shrink: 0;

  display: flex;
  justify-content: flex-end;

  padding-top: 16px;
}
</style>
