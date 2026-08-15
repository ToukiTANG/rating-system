<template>
  <div class="rating-item-page">
    <!-- 搜索区域 -->
    <section class="search-panel">
      <el-form :model="searchForm" inline class="search-form" @submit.prevent>
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
          <span class="table-title">评分项目列表</span>
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

        <el-table-column prop="name" label="项目名称" min-width="150" show-overflow-tooltip />

        <el-table-column prop="description" label="项目描述" min-width="260" show-overflow-tooltip />
        <el-table-column label="区分专家评委" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="row.distinguishExpert ? 'success' : 'info'">
              {{ row.distinguishExpert ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="专家评委占比" width="140" align="center">
          <template #default="{ row }">
            <span v-if="row.distinguishExpert && row.expertWeight !== null">
              {{ formatExpertWeight(row.expertWeight) }}
            </span>

            <span v-else class="empty-value"> -- </span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type">
              {{ statusMap[row.status]?.label ?? '未知状态' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180" fixed="right" align="center" class-name="operation-column">
          <template #default="{ row }">
            <el-button type="primary" :disabled="row.status !== 0" link @click="handleEdit(row)"> 编辑 </el-button>
            <el-button type="warning" :disabled="row.status === 3" link @click="handleRating(row)"> 评分 </el-button>
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
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { RatingItem, SearchForm } from '@/types'
import { deleteRatingItem, getRatingItemList } from '@/api/rating/rating.ts'
import AddOrUpdate from '@/views/rating/AddOrUpdate.vue'
import { useRouter } from 'vue-router'

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

const searchForm = reactive<SearchForm>({
  name: '',
  status: null,
})

const pagination = reactive<Pagination>({
  page: 1,
  pageSize: 10,
  total: 3,
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
 * 查询
 */
function handleSearch() {
  pagination.page = 1

  console.log('搜索条件:', {
    ...searchForm,
    page: pagination.page,
    pageSize: pagination.pageSize,
  })

  loadData()
}

/**
 * 重置查询条件
 */
function handleReset() {
  searchForm.name = ''
  searchForm.status = null

  pagination.page = 1

  loadData()
}

/**
 * 格式化专家评委占比。
 *
 * 后端存储：
 * 0.6
 *
 * 页面展示：
 * 60%
 */
function formatExpertWeight(expertWeight: number): string {
  return `${Math.round(expertWeight * 100)}%`
}

/**
 * 加载数据
 */
async function loadData() {
  loading.value = true

  try {
    const response = await getRatingItemList({
      name: searchForm.name || undefined,
      status: searchForm.status || undefined,
      page: pagination.page,
      pageSize: pagination.pageSize,
    })

    tableData.value = response.list
    pagination.total = response.total

    console.log('load rating items')
  } finally {
    loading.value = false
  }
}

/**
 * 打开新增弹窗。
 */
function handleAdd() {
  // 新增时必须清空当前编辑对象，
  // AddOrUpdate 会据此判断当前是新增模式。
  currentItem.value = null

  dialogVisible.value = true
}

/**
 * 打开编辑弹窗。
 */
function handleEdit(row: RatingItem) {
  /**
   * 建议复制一份 row。
   *
   * 避免子组件修改表单时，
   * 意外直接影响表格中的原始对象。
   */
  currentItem.value = {
    ...row,
  }

  dialogVisible.value = true
}

/**
 * 跳转评分页面
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
  /**
   * 新增数据通常按 ID 倒序排列，
   * 因此新增成功后跳到第一页，
   * 方便立即看到刚新增的数据。
   */
  if (mode === 'add') {
    pagination.page = 1
  }

  /**
   * 重新查询数据库中的最新数据。
   */
  loadData()
}

/**
 * 删除
 */
async function handleDelete(row: RatingItem) {
  try {
    await ElMessageBox.confirm(`确认删除评分项目「${row.name}」吗？`, '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })

    await deleteRatingItem(row.id)
    pagination.page = 1
    await loadData()
    ElMessage.success('删除成功')
  } catch {
    // 用户取消，不需要处理
  }
}

/**
 * 修改每页数量
 */
function handlePageSizeChange(pageSize: number) {
  pagination.pageSize = pageSize
  pagination.page = 1

  loadData()
}

/**
 * 翻页
 */
function handlePageChange(page: number) {
  pagination.page = page

  loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.rating-item-page {
  display: flex;
  flex-direction: column;

  gap: 16px;

  width: 100%;
  height: 100%;

  box-sizing: border-box;
}

/* =========================
   搜索区域
========================= */

.search-panel {
  padding: 20px 20px 2px;

  background: #ffffff;

  border: 1px solid #e5e7eb;
  border-radius: 8px;

  box-sizing: border-box;
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
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
}

.table-title {
  font-size: 16px;
  font-weight: 600;

  color: #303133;
}

:deep(.operation-column) {
  border-left: 1px solid var(--el-table-border-color) !important;
}

.empty-value {
  color: #909399;
}

/* =========================
   分页
========================= */

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;

  margin-top: auto;
  padding-top: 20px;
}
</style>
