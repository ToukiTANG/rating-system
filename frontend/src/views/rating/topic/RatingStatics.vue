<template>
  <div v-loading="loading" class="rating-statistics-page">
    <!-- =========================
         页面顶部
    ========================== -->
    <header class="page-header">
      <div class="header-left">
        <el-button text class="back-button" @click="handleBack">
          <el-icon>
            <ArrowLeft />
          </el-icon>

          返回评分主题
        </el-button>

        <div class="page-title-row">
          <h1 class="page-title">
            {{ statistics?.topicName || '评分统计' }}
          </h1>

          <el-tag v-if="statistics" type="info" effect="plain"> {{ statistics.items.length }} 个评分项目 </el-tag>
        </div>

        <div class="page-description">各评分项目当前得分，按得分从高到低排列</div>
      </div>
    </header>

    <!-- =========================
         页面主体
    ========================== -->
    <div class="page-container">
      <main class="page-content">
        <section class="chart-panel">
          <!-- 图表标题 -->
          <div class="chart-header">
            <div>
              <div class="chart-title">当前排行</div>

              <div class="chart-description">展示各评分项目的当前最终得分</div>
            </div>
          </div>

          <!-- 暂无项目 -->
          <el-empty v-if="!loading && statistics && statistics.items.length === 0" description="当前主题下暂无评分项目" />

          <!-- 图表 -->
          <div
            v-else
            ref="chartRef"
            class="statistics-chart"
            :style="{
              height: `${chartHeight}px`,
            }"
          />
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { ArrowLeft } from '@element-plus/icons-vue'

import { ElMessage } from 'element-plus'

import { useRoute, useRouter } from 'vue-router'

/* =========================
   ECharts 按需引入
========================= */

/**
 * 只引入 ECharts 核心能力。
 *
 * 不再使用：
 *
 * import * as echarts from 'echarts'
 *
 * 避免把完整 ECharts 打入
 * RatingStatics 页面 chunk。
 */
import * as echarts from 'echarts/core'

/**
 * 当前页面只使用柱状图。
 */
import { BarChart } from 'echarts/charts'

/**
 * 当前页面使用：
 *
 * - Grid 直角坐标系
 * - Tooltip 提示框
 */
import { GridComponent, TooltipComponent } from 'echarts/components'

/**
 * 使用 Canvas 渲染器。
 *
 * 按需引入 ECharts 时，
 * Renderer 必须显式注册。
 */
import { CanvasRenderer } from 'echarts/renderers'

/**
 * ECharts Option 类型。
 */
import type { ComposeOption } from 'echarts/core'

import type { BarSeriesOption } from 'echarts/charts'

import type { GridComponentOption, TooltipComponentOption } from 'echarts/components'

import type { RatingTopicItemStatistic, RatingTopicStatistics } from '@/types'

import { getRatingTopicStatistics } from '@/api/rating/RatingTopic.ts'

/**
 * 注册当前页面实际使用的 ECharts 模块。
 *
 * 必须在 echarts.init() 之前执行。
 */
echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

/**
 * 当前页面 ECharts Option 类型。
 *
 * 只声明实际使用的组件，
 * 同时保留完整 TypeScript 类型检查。
 */
type ECOption = ComposeOption<BarSeriesOption | GridComponentOption | TooltipComponentOption>

const route = useRoute()

const router = useRouter()

/* =========================
   图表颜色配置
========================= */

/**
 * 后续需要修改排行榜整体颜色时，
 * 通常只需要修改 baseColor。
 */
const CHART_COLOR_CONFIG = {
  /**
   * 柱状图基准颜色。
   *
   * 所有有评分的柱子均基于该颜色，
   * 再根据排名动态改变透明度。
   */
  baseColor: '#2A6E3F',

  /**
   * 第一名透明度。
   */
  maxOpacity: 0.95,

  /**
   * 最后一名透明度。
   */
  minOpacity: 0.4,

  /**
   * 暂无评分项目颜色。
   */
  emptyColor: '#DCDFE6',

  /**
   * Hover 阴影透明度。
   */
  hoverShadowOpacity: 0.2,
} as const

/**
 * 页面加载状态。
 */
const loading = ref(false)

/**
 * ECharts DOM。
 */
const chartRef = ref<HTMLDivElement | null>(null)

/**
 * ECharts 实例。
 *
 * 使用 ReturnType 避免依赖完整 ECharts
 * namespace 中的实例类型。
 */
let chartInstance: ReturnType<typeof echarts.init> | null = null

/**
 * Topic 统计数据。
 */
const statistics = ref<RatingTopicStatistics | null>(null)

/**
 * 当前 Topic ID。
 */
const topicId = computed<number | null>(() => {
  const id = Number(route.params.topicId)

  if (!Number.isInteger(id) || id <= 0) {
    return null
  }

  return id
})

/**
 * 根据 Item 数量动态计算图表高度。
 *
 * Item 较少时保持基本高度；
 * Item 较多时逐渐扩展，
 * 避免柱状图过于拥挤。
 */
const chartHeight = computed(() => {
  const count = statistics.value?.items.length ?? 0

  return Math.max(360, count * 58 + 80)
})

/**
 * 返回评分主题列表。
 */
function handleBack() {
  router.push({
    name: 'RatingTopic',
  })
}

/**
 * 初始化页面。
 */
async function init() {
  const id = topicId.value

  if (id === null) {
    ElMessage.error('评分主题 ID 无效')

    return
  }

  loading.value = true

  try {
    statistics.value = await getRatingTopicStatistics(id)

    await nextTick()

    renderChart()
  } finally {
    loading.value = false
  }
}

/**
 * 将 HEX 颜色转换为 RGBA。
 *
 * 支持：
 *
 * #315EFB
 * #409EFF
 * #ABC
 *
 * 例如：
 *
 * hexToRgba('#315EFB', 0.8)
 *
 * =>
 *
 * rgba(49, 94, 251, 0.8)
 */
function hexToRgba(hex: string, opacity: number): string {
  const normalized = hex.replace('#', '').trim()

  /**
   * #ABC
   *
   * =>
   *
   * AABBCC
   */
  const value =
    normalized.length === 3
      ? normalized
          .split('')
          .map((char) => `${char}${char}`)
          .join('')
      : normalized

  const red = parseInt(value.slice(0, 2), 16)

  const green = parseInt(value.slice(2, 4), 16)

  const blue = parseInt(value.slice(4, 6), 16)

  return `rgba(${red}, ${green}, ${blue}, ${opacity})`
}

/**
 * 绘制评分排行。
 */
function renderChart() {
  const element = chartRef.value

  const data = statistics.value

  if (!element || !data || data.items.length === 0) {
    return
  }

  /**
   * 页面首次进入时创建 ECharts 实例。
   */
  if (!chartInstance) {
    chartInstance = echarts.init(element)
  }

  /**
   * 后端已经按照 finalScore
   * 从高到低排序。
   *
   * 暂无评分的 Item 位于最后。
   */
  const items = data.items

  /**
   * 当前真正存在评分的 Item。
   *
   * 暂无评分 Item 不参与颜色梯度计算。
   */
  const ratedItems = items.filter((item) => item.finalScore !== null)

  const ratedItemCount = ratedItems.length

  /**
   * 建立：
   *
   * itemId -> 有效排名索引
   *
   * 颜色梯度与真正的评分排名绑定，
   * 不依赖暂无评分 Item 所在的位置。
   */
  const ratedIndexMap = new Map<number, number>()

  ratedItems.forEach((item, index) => {
    ratedIndexMap.set(item.itemId, index)
  })

  /**
   * 根据当前 Item 排名动态计算颜色。
   *
   * 排名越高：
   * opacity 越高，颜色越深。
   *
   * 排名越低：
   * opacity 越低，颜色越浅。
   */
  function getRankColor(item: RatingTopicItemStatistic): string {
    /**
     * 暂无评分：
     * 使用固定灰色。
     */
    if (item.finalScore === null) {
      return CHART_COLOR_CONFIG.emptyColor
    }

    /**
     * 获取该 Item 在有效评分 Item
     * 中的排名位置。
     */
    const rankIndex = ratedIndexMap.get(item.itemId) ?? 0

    /**
     * 只有一个有评分 Item 时，
     * 直接使用最大透明度。
     */
    if (ratedItemCount <= 1) {
      return hexToRgba(
        CHART_COLOR_CONFIG.baseColor,

        CHART_COLOR_CONFIG.maxOpacity,
      )
    }

    /**
     * 排名进度：
     *
     * 第一名：
     * progress = 0
     *
     * 最后一名：
     * progress = 1
     */
    const progress = rankIndex / (ratedItemCount - 1)

    /**
     * opacity 线性插值：
     *
     * maxOpacity
     * ↓
     * minOpacity
     */
    const opacity = CHART_COLOR_CONFIG.maxOpacity - (CHART_COLOR_CONFIG.maxOpacity - CHART_COLOR_CONFIG.minOpacity) * progress

    return hexToRgba(
      CHART_COLOR_CONFIG.baseColor,

      Number(opacity.toFixed(2)),
    )
  }

  /**
   * Hover 时使用基准色阴影。
   */
  const hoverShadowColor = hexToRgba(
    CHART_COLOR_CONFIG.baseColor,

    CHART_COLOR_CONFIG.hoverShadowOpacity,
  )

  const option: ECOption = {
    /**
     * 初始动画。
     */
    animationDuration: 600,

    /**
     * Tooltip。
     */
    tooltip: {
      trigger: 'axis',

      axisPointer: {
        type: 'shadow',
      },

      backgroundColor: 'rgba(255, 255, 255, 0.96)',

      borderColor: '#e5e7eb',

      borderWidth: 1,

      textStyle: {
        color: '#303133',
      },

      extraCssText: 'box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08); border-radius: 8px;',

      formatter(params) {
        const list = Array.isArray(params) ? params : [params]

        const first = list[0]

        if (!first) {
          return ''
        }

        const index = typeof first.dataIndex === 'number' ? first.dataIndex : 0

        const item = items[index]

        if (!item) {
          return ''
        }

        return formatTooltip(item)
      },
    },

    /**
     * 图表绘制区域。
     */
    grid: {
      top: 24,

      left: 24,

      right: 90,

      bottom: 32,

      containLabel: true,
    },

    /**
     * X 轴：最终得分。
     *
     * 不固定 max=100。
     *
     * 混合评分模式下，
     * 最终得分理论上可能超过 100。
     */
    xAxis: {
      type: 'value',

      min: 0,

      axisLine: {
        show: false,
      },

      axisTick: {
        show: false,
      },

      axisLabel: {
        color: '#909399',

        fontSize: 12,
      },

      splitLine: {
        lineStyle: {
          color: '#ebeef5',

          type: 'dashed',
        },
      },
    },

    /**
     * Y 轴：评分项目。
     */
    yAxis: {
      type: 'category',

      /**
       * 后端第一项即最高分。
       *
       * inverse=true 后，
       * 第一项位于图表顶部。
       */
      inverse: true,

      data: items.map((item) => item.itemName),

      axisLine: {
        show: false,
      },

      axisTick: {
        show: false,
      },

      axisLabel: {
        width: 180,

        overflow: 'truncate',

        color: '#606266',

        fontSize: 13,

        margin: 16,
      },
    },

    /**
     * 柱状图。
     */
    series: [
      {
        name: '当前得分',

        type: 'bar',

        barWidth: 24,

        /**
         * 暂无评分 Item：
         *
         * finalScore = null
         *
         * ECharts 中使用 0 作为绘制值，
         * 实际展示仍然根据 finalScore
         * 判断“0分”还是“暂无评分”。
         */
        data: items.map((item) => ({
          value: item.finalScore ?? 0,
        })),

        /**
         * 柱状图颜色。
         */
        itemStyle: {
          color(params) {
            const item = items[params.dataIndex]

            if (!item) {
              return CHART_COLOR_CONFIG.emptyColor
            }

            return getRankColor(item)
          },

          borderRadius: [0, 5, 5, 0],
        },

        /**
         * 鼠标 Hover 状态。
         */
        emphasis: {
          itemStyle: {
            opacity: 1,

            shadowBlur: 8,

            shadowColor: hoverShadowColor,
          },
        },

        /**
         * 柱子右侧标签。
         */
        label: {
          show: true,

          position: 'right',

          distance: 8,

          color: '#606266',

          fontSize: 12,

          formatter(params) {
            const item = items[params.dataIndex]

            if (!item) {
              return ''
            }

            /**
             * 暂无评分。
             */
            if (item.finalScore === null) {
              return '暂无评分'
            }

            /**
             * 正常得分：
             * 保留两位小数。
             */
            return item.finalScore.toFixed(2)
          },
        },
      },
    ],
  }

  chartInstance.setOption(option, true)

  chartInstance.resize()
}

/**
 * Tooltip 内容。
 */
function formatTooltip(item: RatingTopicItemStatistic) {
  const score = item.finalScore === null ? '暂无评分' : item.finalScore.toFixed(2)

  return [
    `<div style="font-weight:600;margin-bottom:8px;">${escapeHtml(item.itemName)}</div>`,

    `<div>当前得分：<strong>${score}</strong></div>`,

    `<div style="margin-top:4px;">评分人数：${item.ratingCount} 人</div>`,
  ].join('')
}

/**
 * Tooltip HTML 转义。
 *
 * 避免业务数据直接插入 HTML。
 */
function escapeHtml(value: string) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#039;')
}

/**
 * 浏览器窗口变化时，
 * 重新适配 ECharts 尺寸。
 */
function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  window.addEventListener('resize', handleResize)

  init()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)

  chartInstance?.dispose()

  chartInstance = null
})
</script>

<style scoped>
.rating-statistics-page {
  width: 100%;
  min-height: 100vh;

  padding-bottom: 40px;

  background: #f5f7fa;

  box-sizing: border-box;
}

/* =========================
   页面顶部
========================= */

.page-header {
  width: 100%;

  padding: 22px 32px 24px;

  margin-bottom: 20px;

  background: #ffffff;

  border-bottom: 1px solid #e5e7eb;

  box-sizing: border-box;
}

.header-left {
  width: 100%;
  max-width: 1600px;

  margin: 0 auto;

  min-width: 0;
}

.back-button {
  margin-bottom: 16px;

  padding: 0;

  color: #606266;

  font-size: 14px;
}

.back-button:hover {
  color: var(--el-color-primary);
}

.page-title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;

  gap: 12px;
}

.page-title {
  margin: 0;

  color: #303133;

  font-size: 24px;
  font-weight: 600;
  line-height: 32px;
}

.page-description {
  margin-top: 8px;

  color: #909399;

  font-size: 14px;
  line-height: 22px;
}

/* =========================
   页面内容容器
========================= */

.page-container {
  width: calc(100% - 64px);
  max-width: 1600px;

  margin: 0 auto;

  display: flex;
  flex-direction: column;

  gap: 20px;

  box-sizing: border-box;
}

/* =========================
   页面主体
========================= */

.page-content {
  width: 100%;
}

/* =========================
   图表卡片
========================= */

.chart-panel {
  width: 100%;

  padding: 26px 28px 30px;

  background: #ffffff;

  border: 1px solid #e5e7eb;
  border-radius: 10px;

  box-sizing: border-box;
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 12px;
}

.chart-title {
  color: #303133;

  font-size: 17px;
  font-weight: 600;
  line-height: 24px;
}

.chart-description {
  margin-top: 5px;

  color: #909399;

  font-size: 13px;
  line-height: 20px;
}

.statistics-chart {
  width: 100%;

  min-height: 360px;
}

/* =========================
   小屏幕适配
========================= */

@media (max-width: 768px) {
  .rating-statistics-page {
    padding-bottom: 24px;
  }

  .page-header {
    padding: 18px 16px 20px;

    margin-bottom: 16px;
  }

  .page-container {
    width: calc(100% - 32px);

    gap: 16px;
  }

  .chart-panel {
    padding: 20px 16px 24px;
  }

  .page-title {
    font-size: 20px;

    line-height: 28px;
  }

  .page-description {
    font-size: 13px;
  }
}
</style>
