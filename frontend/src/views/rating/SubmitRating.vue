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

            <el-tag v-if="reviewerType !== null" :type="reviewerType === 1 ? 'warning' : 'info'" size="large">
              {{ reviewerType === 1 ? '专家评委' : '大众评委' }}
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
        <!-- 当前 Topic 没有正在评分的 Item -->
        <el-empty v-if="!loading && !ratingItem" :description="emptyMessage || '当前暂无正在评分的项目'" />

        <!-- 当前存在正在评分的 Item -->
        <template v-else-if="ratingItem">
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
              <!-- 专家 -->
              <template v-if="reviewerType === 1">
                <span class="submitted-score-value">
                  您提交的评分：
                  <strong>
                    {{ submittedScore }}
                  </strong>
                  分
                </span>
              </template>

              <!-- 大众 -->
              <template v-else>
                <div class="submitted-like">
                  <span class="submitted-like-icons">
                    {{ submittedScore === 2 ? '👍 👍' : '👍' }}
                  </span>

                  <span class="submitted-score-value">
                    您提交了
                    <strong>
                      {{ submittedScore }}
                    </strong>
                    个赞
                  </span>
                </div>
              </template>
            </div>
          </template>

          <!-- 可以评分 -->
          <!-- 可以评分 -->
          <template v-else>
            <!-- =========================
                 专家评分
            ========================== -->
            <template v-if="reviewerType === 1">
              <div class="score-title">请为该项目评分</div>

              <div class="score-description">专家评分采用 0 ～ 100 分制，提交后无法修改。</div>

              <div class="expert-score">
                <el-input-number v-model="score" :min="0" :max="100" :step="1" :precision="0" controls-position="right" size="large" />

                <span class="expert-score-unit"> 分 </span>
              </div>

              <div class="score-value">
                <template v-if="score !== null">
                  当前评分：
                  <strong>
                    {{ score }}
                  </strong>
                  分
                </template>

                <template v-else> 请输入评分 </template>
              </div>
            </template>

            <!-- =========================
                 大众评分
            ========================== -->
            <template v-else-if="reviewerType === 0">
              <div class="score-title">请为该项目点赞</div>

              <div class="score-description">请选择 1 个赞或 2 个赞，提交后无法修改。</div>

              <div class="public-like-options">
                <!-- 1 个赞 -->
                <button
                  type="button"
                  class="like-option"
                  :class="{
                    'like-option-active': score === 1,
                  }"
                  @click="score = 1"
                >
                  <div class="like-icons">👍</div>

                  <div class="like-option-title">1 个赞</div>
                </button>

                <!-- 2 个赞 -->
                <button
                  type="button"
                  class="like-option"
                  :class="{
                    'like-option-active': score === 2,
                  }"
                  @click="score = 2"
                >
                  <div class="like-icons">👍 👍</div>

                  <div class="like-option-title">2 个赞</div>
                </button>
              </div>

              <div class="score-value">
                <template v-if="score !== null">
                  当前选择：
                  <strong>
                    {{ score }}
                  </strong>
                  个赞
                </template>

                <template v-else> 请选择点赞数量 </template>
              </div>
            </template>

            <!-- 提交按钮 -->
            <el-button type="primary" size="large" class="submit-button" :disabled="!canSubmit" :loading="submitting" @click="handleSubmit">
              提交评分
            </el-button>

            <div v-if="ratingItem && ratingItem.status !== 1" class="status-tip">
              {{ ratingDisabledMessage }}
            </div>
          </template>
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
import { getRatingTopicEntry } from '@/api/rating/RatingTopic.ts'

const route = useRoute()

/**
 * 专家评分凭证。
 *
 * 普通大众评分入口：
 *
 * /score/topic/3
 *
 * 专家评分入口：
 *
 * /score/topic/3?expertToken=xxxx
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
 * 当前没有正在评分的项目时的页面提示。
 */
const emptyMessage = ref('')

/**
 * 当前评委类型。
 *
 * 0 = 大众评委
 * 1 = 专家评委
 */
const reviewerType = ref<0 | 1 | null>(null)

/**
 * 页面初始化状态。
 */
const loading = ref(false)

/**
 * 正在提交评分。
 */
const submitting = ref(false)

/**
 * 当前评分。
 *
 * 专家：
 * 0 ~ 100
 *
 * 大众：
 * 1 或 2，表示点赞数量。
 *
 * null：
 * 尚未选择评分。
 */
const score = ref<number | null>(null)

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
 * 从 URL 获取评分主题 ID。
 *
 * 当前评分入口：
 *
 * /score/topic/:topicId
 */
const topicId = computed<number | null>(() => {
  const id = Number(route.params.topicId)

  if (!Number.isInteger(id) || id <= 0) {
    return null
  }

  return id
})

/**
 * 当前是否允许提交。
 */
const canSubmit = computed(() => {
  if (ratingItem.value?.status !== 1 || submitted.value || reviewerType.value === null || score.value === null) {
    return false
  }

  /**
   * 专家：
   * 0 ~ 100 分。
   */
  if (reviewerType.value === 1) {
    return score.value >= 0 && score.value <= 100
  }

  /**
   * 大众：
   * 只能选择 1 个赞或 2 个赞。
   */
  return score.value === 1 || score.value === 2
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
  if (topicId.value === null) {
    emptyMessage.value = '评分主题 ID 无效'

    ElMessage.error('评分主题 ID 无效')

    return
  }

  loading.value = true

  try {
    await loadCurrentRatingItem()
  } finally {
    loading.value = false
  }
}

/**
 * 根据 Topic 获取当前正在评分的 RatingItem。
 *
 * 流程：
 *
 * Topic
 *   ↓
 * /ratingTopic/entry
 *   ↓
 * activeItem
 *   ↓
 * 查询完整 RatingItem
 *   ↓
 * 查询当前客户端提交状态
 */
async function loadCurrentRatingItem() {
  const id = topicId.value

  if (id === null) {
    ratingItem.value = null
    emptyMessage.value = '评分主题 ID 无效'

    return
  }

  /**
   * 每次重新进入 Topic 时先清理旧 Item 状态。
   *
   * 因为 Topic 当前正在评分的 Item
   * 可能已经发生切换。
   */
  ratingItem.value = null

  score.value = 0

  submitted.value = false
  submittedScore.value = null

  emptyMessage.value = ''

  /**
   * 查询 Topic 当前评分入口。
   *
   * 后端同时会：
   *
   * 1. 判断大众 / 专家身份
   * 2. 找到当前 status=1 的 Item
   * 3. 为当前 Item 申请评分名额
   */
  const entry = await getRatingTopicEntry({
    topicId: id,
    clientId: getClientId(),
    expertToken: expertToken.value ?? undefined,
  })

  reviewerType.value = entry.reviewerType

  if (!entry.activeItem) {
    emptyMessage.value = '当前暂无正在评分的项目'

    return
  }

  /**
   * entry 中只返回当前 active Item 的基础信息。
   *
   * 当前页面还需要 createTime 等完整字段，
   * 因此再查询一次 RatingItem 详情。
   */
  ratingItem.value = await getRatingItem({
    id: entry.activeItem.id,
  })

  /**
   * 查询当前客户端是否已经提交过
   * 当前 Item 的评分。
   */
  await loadRatingStatus()
}

/**
 * 刷新当前 Topic 的评分状态。
 *
 * 注意：
 *
 * Topic 当前正在评分的 RatingItem
 * 可能已经发生变化，因此不能只刷新
 * 当前 ratingItem.status。
 *
 * 必须重新调用 Topic entry。
 */
async function handleRefreshStatus() {
  if (topicId.value === null) {
    ElMessage.error('评分主题 ID 无效')

    return
  }

  refreshing.value = true

  try {
    await loadCurrentRatingItem()

    ElMessage.success('评分状态已刷新')
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

  if (score.value === null || reviewerType.value === null) {
    return
  }

  const confirmMessage = reviewerType.value === 1 ? `确认提交 ${score.value} 分吗？提交后无法修改。` : `确认提交 ${score.value} 个赞吗？提交后无法修改。`

  try {
    await ElMessageBox.confirm(confirmMessage, '提交评分', {
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
      expertToken: expertToken.value ?? undefined,
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

/* =========================
   专家评分
========================= */

.expert-score {
  display: flex;
  align-items: center;

  gap: 10px;

  margin-top: 44px;
}

.expert-score :deep(.el-input-number) {
  width: 200px;
}

.expert-score-unit {
  color: #606266;

  font-size: 16px;
}

/* =========================
   大众点赞
========================= */

.public-like-options {
  display: flex;
  align-items: stretch;
  justify-content: center;

  gap: 24px;

  margin-top: 44px;
}

.like-option {
  width: 180px;
  height: 150px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  border: 2px solid #dcdfe6;
  border-radius: 12px;

  background: #ffffff;

  cursor: pointer;

  transition:
    border-color 0.2s,
    background-color 0.2s,
    transform 0.2s;

  box-sizing: border-box;
}

.like-option:hover {
  border-color: var(--el-color-primary-light-3);

  transform: translateY(-2px);
}

.like-option-active {
  border-color: var(--el-color-primary);

  background: var(--el-color-primary-light-9);
}

.like-icons {
  font-size: 40px;
  line-height: 1;
}

.like-option-title {
  margin-top: 18px;

  color: #303133;

  font-size: 16px;
  font-weight: 600;
}

/* =========================
   已提交点赞
========================= */

.submitted-like {
  display: flex;
  align-items: center;

  gap: 16px;
}

.submitted-like-icons {
  font-size: 32px;
}

.submitted-score-value strong {
  color: #303133;
  font-size: 20px;
}
</style>
