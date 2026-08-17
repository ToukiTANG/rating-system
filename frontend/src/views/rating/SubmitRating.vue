<template>
  <div class="rating-view">
    <!-- =========================
         顶部评分项目信息
    ========================== -->
    <header class="rating-header">
      <div class="header-top">
        <div class="header-left">
          <!-- 项目标题 -->
          <div class="title-row">
            <h1 class="rating-title">
              {{ ratingItem?.name || '评分项目' }}
            </h1>

            <el-tag v-if="ratingItem" :type="statusInfo.type" size="large">
              {{ statusInfo.label }}
            </el-tag>
          </div>

          <!-- 项目描述 -->
          <div class="description">
            {{ ratingItem?.description || '-' }}
          </div>
        </div>
      </div>

      <!-- 项目辅助信息 -->
      <div v-if="ratingItem" class="meta-info">
        <div class="meta-item">
          <span class="meta-label"> 项目 ID </span>

          <span class="meta-value">
            {{ ratingItem.id }}
          </span>
        </div>

        <div class="meta-item">
          <span class="meta-label"> 创建时间 </span>

          <span class="meta-value">
            {{ ratingItem.createTime }}
          </span>
        </div>
      </div>

      <!-- 右侧操作 -->
      <div class="header-actions">
        <el-button :loading="refreshing" @click="handleRefreshStatus">
          <el-icon>
            <Refresh />
          </el-icon>

          刷新状态
        </el-button>
      </div>
    </header>

    <!-- =========================
         页面主体
    ========================== -->
    <main v-loading="loading" class="rating-content">
      <section class="score-panel">
        <!-- 已经提交 -->
        <template v-if="submitted">
          <div class="submitted-icon">
            <el-icon>
              <CircleCheck />
            </el-icon>
          </div>

          <div class="submitted-title">评分已提交</div>

          <div class="submitted-description">您已经完成本次评分，无法再次提交。</div>

          <div v-if="submittedScore !== null" class="submitted-score">
            <el-rate :model-value="submittedScore" disabled size="large" />

            <span class="submitted-score-value"> {{ submittedScore.toFixed(1) }} 分 </span>
          </div>
        </template>

        <!-- 可以评分 -->
        <template v-else>
          <div class="score-title">请为该项目评分</div>

          <div class="score-description">请选择 1 ～ 5 分，提交后无法修改。</div>

          <!-- 评分控件 -->
          <div class="score-rate">
            <el-rate v-model="score" :max="5" size="large" show-score score-template="{value} 分" />
          </div>

          <!-- 当前评分 -->
          <div class="score-value">
            <template v-if="score > 0">
              当前评分：
              <strong>{{ score.toFixed(1) }}</strong>
              分
            </template>

            <template v-else> 请选择评分 </template>
          </div>

          <!-- 提交按钮 -->
          <el-button type="primary" size="large" class="submit-button" :disabled="!canSubmit" :loading="submitting" @click="handleSubmit"> 提交评分 </el-button>

          <!-- 项目非评分中 -->
          <div v-if="ratingItem && ratingItem.status !== 1" class="status-tip">
            {{ ratingDisabledMessage }}
          </div>
        </template>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { CircleCheck, Refresh } from '@element-plus/icons-vue'

import { ElMessage, ElMessageBox } from 'element-plus'

import { useRoute } from 'vue-router'

import type { RatingItem } from '@/types'

import { getRatingItem, getRatingStatus, submitScore } from '@/api/rating/rating'

import { getClientId } from '@/utils/client'

const route = useRoute()

/**
 * 专家评分凭证。
 *
 * 普通大众评分入口：
 * /score/12
 *
 * 专家评分入口：
 * /score/12?expertToken=xxxx
 */
const expertToken = computed<string | null>(() => {
  const value = route.query.expertToken

  return typeof value === 'string' ? value : null
})

/**
 * 当前评分项目。
 */
const ratingItem = ref<RatingItem | null>(null)

/**
 * 页面初始化状态。
 */
const loading = ref(false)

/**
 * 正在提交评分。
 */
const submitting = ref(false)

/**
 * 当前用户选择的评分。
 */
const score = ref(0)

/**
 * 当前客户端是否已经提交过评分。
 */
const submitted = ref(false)

/**
 * 当前客户端已经提交的评分。
 */
const submittedScore = ref<number | null>(null)

/**
 * 正在刷新项目状态。
 */
const refreshing = ref(false)

/**
 * 状态显示信息。
 */
const statusMap = {
  0: {
    label: '未开始',
    type: 'info',
  },

  1: {
    label: '评分中',
    type: 'warning',
  },

  2: {
    label: '已结束',
    type: 'success',
  },
} as const

/**
 * 当前项目状态展示。
 */
const statusInfo = computed(() => {
  const item = ratingItem.value

  if (!item) {
    return {
      label: '-',
      type: 'info' as const,
    }
  }

  return statusMap[item.status]
})

/**
 * 从 URL 获取评分项目 ID。
 */
const ratingItemId = computed<number | null>(() => {
  const id = Number(route.params.id)

  if (!Number.isInteger(id) || id <= 0) {
    return null
  }

  return id
})

/**
 * 当前是否允许提交评分。
 */
const canSubmit = computed(() => {
  return ratingItem.value?.status === 1 && !submitted.value && score.value > 0
})

/**
 * 项目不可评分时的提示。
 */
const ratingDisabledMessage = computed(() => {
  const item = ratingItem.value

  if (!item) {
    return ''
  }

  if (item.status === 0) {
    return '评分尚未开始'
  }

  if (item.status === 2) {
    return '评分已经结束'
  }

  return ''
})

/**
 * 页面初始化。
 */
async function init() {
  const id = ratingItemId.value

  if (id === null) {
    ElMessage.error('评分项目 ID 无效')

    return
  }

  loading.value = true

  try {
    /**
     * 如果是从其他页面跳转进来，
     * 优先读取 history.state 中携带的项目数据。
     */
    const stateItem = window.history.state?.item as RatingItem | undefined

    if (stateItem && stateItem.id === id) {
      ratingItem.value = {
        ...stateItem,
      }
    } else {
      /**
       * 刷新页面或者直接访问 URL 时，
       * 根据项目 ID 从后端重新获取。
       */
      ratingItem.value = await getRatingItem({
        id,
      })
    }

    /**
     * 查询当前浏览器是否已经提交过评分。
     */
    await loadRatingStatus()
  } finally {
    loading.value = false
  }
}

/**
 * 刷新评分项目状态。
 *
 * 同时刷新当前浏览器的评分提交状态，
 * 保证页面展示与后端最新状态一致。
 */
async function handleRefreshStatus() {
  const id = ratingItemId.value

  if (id === null) {
    ElMessage.error('评分项目 ID 无效')

    return
  }

  refreshing.value = true

  try {
    /**
     * 重新从后端获取评分项目，
     * 不使用 history.state 中的缓存数据。
     */
    ratingItem.value = await getRatingItem({
      id,
    })

    /**
     * 同时重新查询当前客户端是否已经提交评分。
     */
    await loadRatingStatus()

    ElMessage.success('项目状态已刷新')
  } finally {
    refreshing.value = false
  }
}

/**
 * 查询当前浏览器客户端评分状态。
 */
async function loadRatingStatus() {
  const item = ratingItem.value

  if (!item) {
    return
  }

  const result = await getRatingStatus({
    ratingItemId: item.id,
    clientId: getClientId(),
  })

  submitted.value = result.submitted

  submittedScore.value = result.score
}

/**
 * 提交评分。
 */
async function handleSubmit() {
  const item = ratingItem.value

  if (!item) {
    return
  }

  if (!canSubmit.value) {
    return
  }

  try {
    await ElMessageBox.confirm(`确认提交 ${score.value.toFixed(1)} 分吗？提交后无法修改。`, '提交评分', {
      confirmButtonText: '确认提交',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  submitting.value = true

  try {
    await submitScore({
      ratingItemId: item.id,
      clientId: getClientId(),
      score: score.value,
      expertToken: expertToken.value,
    })

    /**
     * 本地立即切换为已提交状态。
     *
     * 即使用户快速再次点击，
     * 后端数据库 UNIQUE 约束仍然会兜底。
     */
    submitted.value = true

    submittedScore.value = score.value

    ElMessage.success('评分提交成功')
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  init()
})
</script>

<style scoped>
.rating-view {
  width: 100%;
  height: 100vh;

  display: flex;
  flex-direction: column;

  overflow: hidden;

  background: #f5f6f8;

  box-sizing: border-box;
}

/* =========================
   顶部项目信息
========================= */

.rating-header {
  flex-shrink: 0;

  padding: 24px 32px;

  background: #ffffff;

  border-bottom: 1px solid #e5e7eb;

  box-sizing: border-box;
}

.header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;

  gap: 32px;
}

.header-left {
  flex: 1;

  min-width: 0;
}

.header-actions {
  flex-shrink: 0;

  display: flex;
  align-items: center;

  padding-top: 42px;
}

.title-row {
  display: flex;
  align-items: center;

  gap: 12px;
}

.rating-title {
  margin: 0;

  min-width: 0;

  overflow: hidden;

  color: #303133;

  font-size: 24px;
  font-weight: 600;

  text-overflow: ellipsis;
  white-space: nowrap;
}

.description {
  margin-top: 10px;

  max-width: 900px;

  color: #606266;

  font-size: 14px;
  line-height: 22px;
}

/* =========================
   项目辅助信息
========================= */

.meta-info {
  display: flex;
  align-items: center;

  gap: 32px;

  margin-top: 22px;
  padding-top: 18px;

  border-top: 1px solid #f0f2f5;
}

.meta-item {
  display: flex;
  align-items: center;

  gap: 8px;

  font-size: 13px;
}

.meta-label {
  color: #909399;
}

.meta-value {
  color: #606266;
}

/* =========================
   页面主体
========================= */

.rating-content {
  flex: 1;

  min-width: 0;
  min-height: 0;

  display: flex;
  align-items: center;
  justify-content: center;

  padding: 32px;

  box-sizing: border-box;
}

/* =========================
   评分卡片
========================= */

.score-panel {
  width: min(760px, 100%);
  min-height: 420px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 48px;

  background: #ffffff;

  border: 1px solid #e5e7eb;
  border-radius: 12px;

  box-sizing: border-box;
}

.score-title {
  color: #303133;

  font-size: 22px;
  font-weight: 600;
}

.score-description {
  margin-top: 12px;

  color: #909399;

  font-size: 14px;
}

.score-rate {
  margin-top: 44px;
}

.score-value {
  height: 24px;

  margin-top: 26px;

  color: #606266;

  font-size: 15px;
}

.score-value strong {
  color: #303133;

  font-size: 20px;
}

.submit-button {
  width: 180px;

  margin-top: 36px;
}

.status-tip {
  margin-top: 20px;

  color: #e6a23c;

  font-size: 13px;
}

/* =========================
   已提交状态
========================= */

.submitted-icon {
  color: #67c23a;

  font-size: 64px;
  line-height: 1;
}

.submitted-title {
  margin-top: 24px;

  color: #303133;

  font-size: 22px;
  font-weight: 600;
}

.submitted-description {
  margin-top: 12px;

  color: #909399;

  font-size: 14px;
}

.submitted-score {
  display: flex;
  align-items: center;

  gap: 18px;

  margin-top: 36px;
}

.submitted-score-value {
  color: #606266;

  font-size: 16px;
}
</style>
