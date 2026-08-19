<template>
  <div class="rating-view">
    <!-- =========================
         顶部评分项目信息
    ========================== -->
    <header class="rating-header">
      <div class="header-top">
        <!-- 左侧项目信息 -->
        <div class="header-left">
          <!-- 返回按钮 -->
          <el-button link class="back-button" @click="handleBack">
            <el-icon>
              <ArrowLeft />
            </el-icon>

            返回评分项目
          </el-button>

          <!-- 项目信息 -->
          <div class="item-overview">
            <!-- 项目图片 -->
            <el-image
              v-if="ratingItem?.imageUrl"
              :src="ratingItem.imageUrl"
              :preview-src-list="[ratingItem.imageUrl]"
              fit="cover"
              class="item-image"
              preview-teleported
              hide-on-click-modal
            />

            <!-- 项目文字信息 -->
            <div class="item-info">
              <!-- 项目名称和当前状态 -->
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
        </div>

        <!-- 右侧操作按钮 -->
        <div class="header-actions">
          <el-button type="primary" size="large" :disabled="ratingItem?.status !== 0" :loading="starting" @click="handleStartRating"> 开始评分 </el-button>

          <el-button type="danger" size="large" :disabled="ratingItem?.status !== 1" :loading="finishing" @click="handleFinishRating"> 结束评分 </el-button>
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
      </div>
    </header>

    <!-- =========================
         页面主体
    ========================== -->
    <main v-loading="loading" class="rating-content">
      <!-- 实时平均分 -->
      <!-- 实时评分 -->
      <section class="score-panel">
        <!-- =========================
             核心评分区域
        ========================== -->
        <div
          class="score-overview"
          :class="{
            'score-overview-distinguish': statistics.distinguishExpert,
          }"
        >
          <!-- =========================
               专家评分
          ========================== -->
          <div v-if="statistics.distinguishExpert" class="reviewer-stat">
            <div class="reviewer-stat-title">专家评分</div>

            <div class="reviewer-stat-count">
              <strong>
                {{ statistics.expertCount }}
              </strong>
              <span>人</span>
            </div>

            <div class="reviewer-stat-detail">
              平均分

              <strong>
                {{ statistics.expertAverageScore === null ? '--' : statistics.expertAverageScore.toFixed(2) }}
              </strong>
            </div>

            <div class="reviewer-stat-detail reviewer-stat-weighted">
              加权得分

              <strong>
                {{ statistics.expertWeightedScore.toFixed(2) }}
              </strong>
            </div>
          </div>

          <!-- =========================
               最终实时得分
          ========================== -->
          <div class="final-score">
            <div class="score-title">实时得分</div>

            <div class="score-content">
              <span class="score-value">
                {{ statistics.ratingCount === 0 ? '--' : statistics.finalScore.toFixed(2) }}
              </span>
            </div>
          </div>

          <!-- =========================
               大众评分
          ========================== -->
          <div v-if="statistics.distinguishExpert" class="reviewer-stat">
            <div class="reviewer-stat-title">大众评分</div>

            <div class="reviewer-stat-count">
              <strong>
                {{ statistics.publicCount }}
              </strong>
              <span>人</span>
            </div>

            <div class="reviewer-stat-detail">
              点赞总数

              <strong>
                {{ statistics.publicLikeCount }}
              </strong>
            </div>

            <div class="reviewer-stat-detail reviewer-stat-weighted">
              加权得分

              <strong>
                {{ statistics.publicWeightedScore.toFixed(2) }}
              </strong>
            </div>
          </div>
        </div>

        <!-- 无数据提示 -->
        <div v-if="statistics.ratingCount === 0" class="score-empty">暂无评分数据</div>

        <!-- 最后更新时间 -->
        <div v-else class="score-update-time">
          最后更新：
          {{ formatDateTime(statistics.updateTime) || '-' }}
        </div>

        <!-- 评分中提示 -->
        <div v-if="ratingItem?.status === 1" class="rating-running">
          <span class="running-dot" />

          正在评分，数据将自动更新
        </div>

        <!-- 评分完成提示 -->
        <div v-else-if="ratingItem?.status === 2" class="rating-finished">评分已结束</div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'

import { ElMessage, ElMessageBox } from 'element-plus'

import { ArrowLeft } from '@element-plus/icons-vue'

import { useRoute, useRouter } from 'vue-router'

import type { RatingItem, RatingStatistics } from '@/types'

import { finishRating, getRatingItem, getRatingStatistics, startRating } from '@/api/rating/rating'
import { formatDateTime } from '@/utils/date.ts'

const route = useRoute()

const router = useRouter()

/**
 * 当前评分项目。
 *
 * 页面初始化时优先使用 RatingItem 页面通过
 * history.state 传递的数据。
 *
 * 如果用户刷新页面或直接访问 URL，
 * 则根据路由 ID 从后端重新查询。
 */
const ratingItem = ref<RatingItem | null>(null)

/**
 * 页面初始化 loading。
 */
const loading = ref(false)

/**
 * 开始评分按钮 loading。
 */
const starting = ref(false)

/**
 * 结束评分按钮 loading。
 */
const finishing = ref(false)

/**
 * 当前评分统计信息。
 */
const statistics = reactive<RatingStatistics>({
  finalScore: 0,

  ratingCount: 0,

  distinguishExpert: false,

  expertCount: 0,
  expertAverageScore: null,
  expertWeightedScore: 0,

  publicCount: 0,
  publicLikeCount: 0,
  publicWeightedScore: 0,

  updateTime: null,
})

/**
 * 评分状态对应的展示信息。
 */
const statusMap = {
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
} as const

/**
 * 当前评分项目状态。
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
 * 当前评分项目 ID。
 *
 * 路由：
 *
 * /rating/12
 *
 * 则 ratingItemId = 12。
 */
const ratingItemId = computed<number | null>(() => {
  const id = Number(route.params.id)

  if (!Number.isInteger(id) || id <= 0) {
    return null
  }

  return id
})

/**
 * 实时统计轮询定时器。
 */
let statisticsTimer: number | null = null

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
     * 优先读取 RatingItem 页面跳转时
     * 通过 history.state 传递的数据。
     */
    const stateItem = window.history.state?.item as RatingItem | undefined

    if (stateItem && stateItem.id === id) {
      ratingItem.value = {
        ...stateItem,
      }
    } else {
      /**
       * 用户刷新页面、直接输入 URL 等情况下，
       * history.state 中可能没有完整项目数据。
       *
       * 此时根据 ID 从后端重新查询。
       */
      ratingItem.value = await getRatingItem({
        id,
      })
    }

    /**
     * 页面进入后先获取一次当前统计结果。
     */
    await loadStatistics()

    /**
     * 如果项目当前已经处于评分中，
     * 自动恢复实时统计轮询。
     */
    if (ratingItem.value.status === 1) {
      startStatisticsPolling()
    }
  } finally {
    loading.value = false
  }
}

/**
 * 获取当前评分项目的实时统计数据。
 */
async function loadStatistics() {
  const item = ratingItem.value

  if (!item) {
    return
  }

  const result = await getRatingStatistics({
    id: item.id,
  })

  statistics.finalScore = result.finalScore

  statistics.ratingCount = result.ratingCount

  statistics.distinguishExpert = result.distinguishExpert

  statistics.expertCount = result.expertCount

  statistics.expertAverageScore = result.expertAverageScore

  statistics.publicCount = result.publicCount

  statistics.expertWeightedScore = result.expertWeightedScore

  statistics.publicLikeCount = result.publicLikeCount

  statistics.publicWeightedScore = result.publicWeightedScore

  statistics.updateTime = result.updateTime
}

/**
 * 开始实时统计轮询。
 */
function startStatisticsPolling() {
  /**
   * 避免重复创建多个 setInterval。
   */
  stopStatisticsPolling()

  statisticsTimer = window.setInterval(() => {
    loadStatistics()
  }, 1500)
}

/**
 * 停止实时统计轮询。
 */
function stopStatisticsPolling() {
  if (statisticsTimer === null) {
    return
  }

  window.clearInterval(statisticsTimer)

  statisticsTimer = null
}

/**
 * 开始评分。
 */
async function handleStartRating() {
  const item = ratingItem.value

  if (!item) {
    return
  }

  /**
   * 只有初始化状态才能开始评分。
   */
  if (item.status !== 0) {
    return
  }

  try {
    await ElMessageBox.confirm(`确认开始评分项目「${item.name}」吗？`, '开始评分', {
      confirmButtonText: '开始评分',
      cancelButtonText: '取消',
      type: 'info',
    })
  } catch {
    return
  }

  starting.value = true

  try {
    /**
     * 调用后端开始评分接口。
     *
     * 后端负责完成：
     *
     * status: 0 -> 1
     */
    const result = await startRating({
      id: item.id,
    })

    /**
     * 项目状态以后端返回结果为准。
     */
    ratingItem.value = result

    ElMessage.success('评分已开始')

    /**
     * 开始评分后立即刷新一次统计结果。
     */
    await loadStatistics()

    /**
     * 开始实时轮询平均分。
     */
    startStatisticsPolling()
  } finally {
    starting.value = false
  }
}

/**
 * 结束评分。
 */
async function handleFinishRating() {
  const item = ratingItem.value

  if (!item) {
    return
  }

  /**
   * 只有正在评分状态才能结束评分。
   */
  if (item.status !== 1) {
    return
  }

  try {
    await ElMessageBox.confirm(`确认结束评分项目「${item.name}」吗？结束后将停止继续评分。`, '结束评分', {
      confirmButtonText: '结束评分',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }

  finishing.value = true

  try {
    /**
     * 项目状态以后端返回结果为准。
     */
    ratingItem.value = await finishRating({
      id: item.id,
    })

    /**
     * 评分已经结束，
     * 停止实时轮询。
     */
    stopStatisticsPolling()

    /**
     * 最后再获取一次最终平均分。
     */
    await loadStatistics()

    ElMessage.success('评分已结束')
  } finally {
    finishing.value = false
  }
}

/**
 * 返回评分项目列表。
 */
function handleBack() {
  /**
   * 离开页面前主动停止轮询。
   */
  stopStatisticsPolling()

  router.push({
    name: 'RatingItem',
  })
}

/**
 * 页面加载后初始化数据。
 */
onMounted(() => {
  init()
})

/**
 * 页面销毁时停止轮询，
 * 避免定时器在后台继续请求接口。
 */
onBeforeUnmount(() => {
  stopStatisticsPolling()
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

.back-button {
  margin-bottom: 16px;

  padding-left: 0;
}

/* =========================
   项目信息
========================= */

.item-overview {
  display: flex;
  align-items: center;

  gap: 20px;

  min-width: 0;
}

.item-image {
  width: 140px;
  height: 105px;

  flex-shrink: 0;

  display: block;

  overflow: hidden;

  border: 1px solid #e5e7eb;
  border-radius: 8px;

  background: #f5f7fa;

  cursor: pointer;
}

.item-info {
  flex: 1;

  min-width: 0;
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

.header-actions {
  flex-shrink: 0;

  display: flex;
  align-items: center;

  gap: 12px;

  padding-top: 42px;
}

/* =========================
   项目元数据
========================= */

.meta-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;

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
   实时平均分区域
========================= */

.score-panel {
  width: min(900px, 100%);
  min-height: 400px;

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
  margin-bottom: 30px;

  color: #606266;

  font-size: 17px;
  font-weight: 500;
}

.score-content {
  display: flex;
  align-items: baseline;
  justify-content: center;
}

.score-value {
  color: #303133;

  font-size: 82px;
  font-weight: 600;
  line-height: 1;

  letter-spacing: -2px;
}

.score-total {
  margin-left: 14px;

  color: #909399;

  font-size: 24px;
  font-weight: 400;
}

.score-empty {
  margin-top: 28px;

  color: #909399;

  font-size: 14px;
}

.score-update-time {
  margin-top: 28px;

  color: #909399;

  font-size: 13px;
}

/* =========================
   实时评分总览
========================= */

.score-overview {
  width: 100%;

  display: flex;
  align-items: center;
  justify-content: center;
}

/* 区分专家和大众时：
   左 / 中 / 右三栏布局。 */
.score-overview-distinguish {
  display: grid;

  grid-template-columns:
    minmax(160px, 1fr)
    minmax(260px, 1.4fr)
    minmax(160px, 1fr);

  align-items: center;

  gap: 32px;
}

/* =========================
   中间最终得分
========================= */

.final-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  min-width: 0;
}

.score-title {
  margin-bottom: 30px;

  color: #606266;

  font-size: 17px;
  font-weight: 500;
}

.score-content {
  display: flex;
  align-items: baseline;
  justify-content: center;
}

.score-value {
  color: #303133;

  font-size: 82px;
  font-weight: 600;
  line-height: 1;

  letter-spacing: -2px;
}

/* =========================
   专家 / 大众统计
========================= */

.reviewer-stat {
  min-height: 150px;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  padding: 20px;

  background: #f8f9fb;

  border: 1px solid #ebeef5;
  border-radius: 10px;

  box-sizing: border-box;
}

.reviewer-stat-title {
  color: #606266;

  font-size: 15px;
  font-weight: 500;
}

.reviewer-stat-count {
  margin-top: 18px;

  display: flex;
  align-items: baseline;

  gap: 5px;

  color: #909399;

  font-size: 14px;
}

.reviewer-stat-count strong {
  color: #303133;

  font-size: 30px;
  font-weight: 600;
}

.reviewer-stat-detail {
  margin-top: 12px;

  color: #909399;

  font-size: 13px;
}

.reviewer-stat-detail strong {
  margin-left: 6px;

  color: #606266;

  font-size: 16px;
  font-weight: 600;
}

.reviewer-stat-weighted {
  margin-top: 10px;

  padding-top: 10px;

  width: 100%;

  text-align: center;

  border-top: 1px solid #ebeef5;
}

.reviewer-stat-weighted strong {
  color: #303133;

  font-size: 18px;
  font-weight: 600;
}

/* =========================
   评分状态辅助提示
========================= */

.rating-running {
  margin-top: 24px;

  display: flex;
  align-items: center;

  gap: 8px;

  color: #e6a23c;

  font-size: 13px;
}

.running-dot {
  width: 8px;
  height: 8px;

  flex-shrink: 0;

  border-radius: 50%;

  background: currentColor;

  animation: running-pulse 1.5s infinite;
}

.rating-finished {
  margin-top: 24px;

  color: #67c23a;

  font-size: 13px;
}

@keyframes running-pulse {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0.3;
  }

  100% {
    opacity: 1;
  }
}
</style>
