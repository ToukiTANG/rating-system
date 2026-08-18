<template>
  <div class="rating-topic-page">
    <!-- 搜索区域 -->
    <section class="search-panel">
      <el-form :inline="true" @submit.prevent>
        <el-form-item label="主题名称">
          <el-input v-model="queryParams.name" placeholder="请输入评分主题名称" clearable @keyup.enter="handleSearch" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch"> 查询 </el-button>

          <el-button @click="handleReset"> 重置 </el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- 表格区域 -->
    <section class="table-panel">
      <div class="table-toolbar">
        <div class="table-title">评分主题</div>

        <el-button type="primary" @click="handleAdd"> 新增主题 </el-button>
      </div>

      <div class="table-wrapper">
        <el-table v-loading="loading" :data="topicList" height="100%" border>
          <el-table-column prop="name" label="主题名称" min-width="160" />

          <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />

          <el-table-column label="评委模式" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.distinguishExpert ? 'success' : 'info'">
                {{ formatExpertMode(row) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="专家占比" width="100" align="center">
            <template #default="{ row }">
              {{ formatExpertWeight(row) }}
            </template>
          </el-table-column>

          <el-table-column prop="publicLimit" label="大众人数" width="100" align="center" />

          <el-table-column prop="expertLimit" label="专家人数" width="100" align="center">
            <template #default="{ row }">
              {{ row.expertLimit ?? '-' }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="220" fixed="right" align="center">
            <template #default="{ row }">
              <el-button link type="primary" @click="handleUpdate(row)"> 编辑 </el-button>
              <el-button link type="warning" @click="handleGenerateQrCode(row)"> 生成二维码 </el-button>
              <el-button link type="danger" @click="handleDelete(row)"> 删除 </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handlePageSizeChange"
        />
      </div>

      <AddOrUpdate ref="addOrUpdateRef" @success="loadData" />
      <QrCodeDialog v-model="qrCodeDialogVisible" :topic="qrCodeTopic" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { ElMessage, ElMessageBox } from 'element-plus'

import { deleteRatingTopic, queryRatingTopic } from '@/api/rating/RatingTopic.ts'

import type { RatingTopic, RatingTopicQueryParams } from '@/types'
import AddOrUpdate from '@/views/rating/topic/AddOrUpdate.vue'
import QrCodeDialog from '@/views/rating/topic/QrCodeDialog.vue'

const loading = ref(false)

const topicList = ref<RatingTopic[]>([])

const total = ref(0)

const addOrUpdateRef = ref<InstanceType<typeof AddOrUpdate>>()

const qrCodeDialogVisible = ref(false)

const qrCodeTopic = ref<RatingTopic | null>(null)

const queryParams = reactive<
  Required<Pick<RatingTopicQueryParams, 'page' | 'pageSize'>> & {
    name: string
  }
>({
  name: '',
  page: 1,
  pageSize: 10,
})

async function loadData() {
  loading.value = true

  try {
    const result = await queryRatingTopic({
      name: queryParams.name || undefined,
      page: queryParams.page,
      pageSize: queryParams.pageSize,
    })

    topicList.value = result.list
    total.value = result.total
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1

  loadData()
}

function handleReset() {
  queryParams.name = ''
  queryParams.page = 1

  loadData()
}

function handlePageChange(page: number) {
  queryParams.page = page

  loadData()
}

function handlePageSizeChange(pageSize: number) {
  queryParams.pageSize = pageSize
  queryParams.page = 1

  loadData()
}

/**
 * 生成 Topic 二维码。
 */
function handleGenerateQrCode(row: RatingTopic) {
  qrCodeTopic.value = row

  qrCodeDialogVisible.value = true
}

function handleAdd() {
  addOrUpdateRef.value?.openAdd()
}

function handleUpdate(row: RatingTopic) {
  addOrUpdateRef.value?.openUpdate(row)
}

async function handleDelete(row: RatingTopic) {
  await ElMessageBox.confirm(`确认删除评分主题“${row.name}”吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '确认',
    cancelButtonText: '取消',
  })

  await deleteRatingTopic({
    id: row.id,
  })

  ElMessage.success('删除成功')

  // 当前页只剩最后一条时，
  // 删除后回到上一页。
  if (topicList.value.length === 1 && queryParams.page > 1) {
    queryParams.page -= 1
  }

  await loadData()
}

function formatExpertMode(row: RatingTopic) {
  return row.distinguishExpert ? '区分专家' : '仅大众'
}

function formatExpertWeight(row: RatingTopic) {
  if (!row.distinguishExpert || row.expertWeight == null) {
    return '-'
  }

  return `${Math.round(row.expertWeight * 100)}%`
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.rating-topic-page {
  display: flex;
  flex-direction: column;

  gap: 16px;

  width: 100%;
  height: 100%;

  box-sizing: border-box;
}

.search-panel {
  padding: 16px 16px 0;
  background: var(--el-bg-color);
  border-radius: 8px;
}

.table-panel {
  flex: 1;
  min-height: 0;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;

  display: flex;
  flex-direction: column;
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.table-title {
  font-size: 16px;
  font-weight: 600;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
