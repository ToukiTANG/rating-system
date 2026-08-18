<template>
  <div class="rating-result-page">
    <!-- =========================
         查询条件
    ========================== -->
    <section class="search-panel">
      <el-form :model="searchForm" inline>
        <el-form-item label="评分项目">
          <el-input v-model="searchForm.itemName" placeholder="请输入项目名称" clearable style="width: 220px" @keyup.enter="handleSearch" />
        </el-form-item>

        <el-form-item label="评委类型">
          <el-select v-model="searchForm.reviewerType" placeholder="全部" clearable style="width: 140px">
            <el-option label="大众评委" :value="0" />

            <el-option label="专家评委" :value="1" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch"> 查询 </el-button>

          <el-button @click="handleReset"> 重置 </el-button>
        </el-form-item>
      </el-form>
    </section>

    <!-- =========================
         评分结果表格
    ========================== -->
    <section class="table-panel">
      <div class="table-header">
        <div class="table-title">评分记录</div>

        <div class="table-total">共 {{ pagination.total }} 条评分</div>
      </div>

      <div class="table-wrapper">
        <el-table v-loading="loading" :data="tableData" border height="100%">
          <el-table-column prop="ratingItemName" label="评分项目" min-width="200" show-overflow-tooltip />

          <el-table-column label="评委类型" width="130" align="center">
            <template #default="{ row }">
              <el-tag :type="row.reviewerType === 1 ? 'warning' : 'info'">
                {{ row.reviewerType === 1 ? '专家评委' : '大众评委' }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- =========================
               评分 / 点赞
          ========================== -->
          <el-table-column label="评分结果" width="180" align="center">
            <template #default="{ row }">
              <!-- 专家评分 -->
              <div v-if="row.reviewerType === 1" class="expert-score-cell">
                <span class="expert-score-number">
                  {{ formatExpertScore(row.score) }}
                </span>

                <span class="score-unit"> 分 </span>
              </div>

              <!-- 大众点赞 -->
              <div v-else class="public-score-cell">
                <span class="like-icons">
                  {{ row.score === 2 ? '👍 👍' : '👍' }}
                </span>

                <span class="like-count"> {{ row.score }} 个赞 </span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="客户端 ID" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              {{ formatClientId(row.clientId) }}
            </template>
          </el-table-column>

          <el-table-column label="提交时间" width="180" align="center">
            <template #default="{ row }">
              {{ formatDateTime(row.createTime) }}
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- =========================
           分页
      ========================== -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadData"
          @size-change="handleSizeChange"
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import type { RatingResultItem, ReviewerType } from '@/types'

import { queryRatingResults } from '@/api/rating/rating'

import { formatDateTime } from '@/utils/date.ts'

/**
 * 查询条件。
 */
const searchForm = reactive<{
  itemName: string
  reviewerType: ReviewerType | null
}>({
  itemName: '',
  reviewerType: null,
})

/**
 * 表格加载状态。
 */
const loading = ref(false)

/**
 * 表格数据。
 */
const tableData = ref<RatingResultItem[]>([])

/**
 * 分页信息。
 */
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

/**
 * 查询评分结果。
 */
async function loadData() {
  loading.value = true

  try {
    const result = await queryRatingResults({
      page: pagination.page,

      pageSize: pagination.pageSize,

      itemName: searchForm.itemName.trim() || undefined,

      /**
       * reviewerType = 0 是合法值，
       * 因此这里必须使用 ??，
       * 不能使用 ||。
       */
      reviewerType: searchForm.reviewerType ?? undefined,
    })

    tableData.value = result.list

    pagination.total = result.total
  } finally {
    loading.value = false
  }
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
function handleReset() {
  searchForm.itemName = ''

  searchForm.reviewerType = null

  pagination.page = 1

  loadData()
}

/**
 * 修改每页数量。
 */
function handleSizeChange() {
  pagination.page = 1

  loadData()
}

/**
 * 格式化专家评分。
 *
 * 专家评分采用 0 ~ 100 分制。
 *
 * 当前后端 score 类型仍然为 float，
 * 因此这里兼容整数和小数。
 */
function formatExpertScore(score: number): string {
  if (Number.isInteger(score)) {
    return score.toString()
  }

  return score.toFixed(1)
}

/**
 * 客户端 ID 只展示部分内容。
 */
function formatClientId(clientId: string): string {
  if (clientId.length <= 16) {
    return clientId
  }

  return `${clientId.slice(0, 8)}...${clientId.slice(-8)}`
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.rating-result-page {
  height: 100%;

  display: flex;
  flex-direction: column;

  gap: 16px;
}

/* =========================
   查询区域
========================= */

.search-panel {
  flex-shrink: 0;

  padding: 20px 20px 2px;

  background: #ffffff;

  border-radius: 8px;
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

  border-radius: 8px;

  box-sizing: border-box;
}

.table-header {
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
}

.table-total {
  color: #909399;

  font-size: 13px;
}

.table-wrapper {
  flex: 1;

  min-height: 0;
}

/* =========================
   专家评分
========================= */

.expert-score-cell {
  display: flex;
  align-items: baseline;
  justify-content: center;

  gap: 4px;
}

.expert-score-number {
  color: #303133;

  font-size: 18px;
  font-weight: 600;
}

.score-unit {
  color: #909399;

  font-size: 13px;
}

/* =========================
   大众点赞
========================= */

.public-score-cell {
  display: flex;
  align-items: center;
  justify-content: center;

  gap: 10px;
}

.like-icons {
  font-size: 20px;

  white-space: nowrap;
}

.like-count {
  color: #606266;

  font-size: 14px;
  font-weight: 500;
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
