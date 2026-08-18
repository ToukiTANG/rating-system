<template>
  <el-dialog v-model="visible" title="评分二维码" width="720px" destroy-on-close append-to-body @closed="handleClosed">
    <div v-if="topic" v-loading="loading" class="qr-dialog">
      <!-- 评分主题信息 -->
      <div class="topic-info">
        <div class="topic-name">
          {{ topic.name }}
        </div>

        <div class="topic-description">
          {{ topic.description || '-' }}
        </div>
      </div>

      <!-- 二维码区域 -->
      <div
        class="qr-list"
        :class="{
          'qr-list-single': !topic.distinguishExpert,
        }"
      >
        <!-- =========================
             大众评分二维码
        ========================== -->
        <div class="qr-card">
          <div class="qr-card-header">
            <span class="qr-card-title"> 大众评分 </span>

            <el-tag type="info"> 大众 </el-tag>
          </div>

          <div class="qr-image-wrapper">
            <img v-if="publicQrCode" :src="publicQrCode" alt="大众评分二维码" class="qr-image" />
          </div>

          <div class="qr-url">
            {{ publicUrl }}
          </div>

          <el-button class="copy-button" @click="handleCopy(publicUrl)">
            <el-icon>
              <CopyDocument />
            </el-icon>

            复制链接
          </el-button>
        </div>

        <!-- =========================
             专家评分二维码
        ========================== -->
        <div v-if="topic.distinguishExpert" class="qr-card">
          <div class="qr-card-header">
            <span class="qr-card-title"> 专家评分 </span>

            <el-tag type="warning"> 专家 </el-tag>
          </div>

          <div class="qr-image-wrapper">
            <img v-if="expertQrCode" :src="expertQrCode" alt="专家评分二维码" class="qr-image" />
          </div>

          <div class="qr-url">
            {{ expertUrl }}
          </div>

          <el-button class="copy-button" :disabled="!expertUrl" @click="handleCopy(expertUrl)">
            <el-icon>
              <CopyDocument />
            </el-icon>

            复制链接
          </el-button>
        </div>
      </div>

      <!-- 专家提示 -->
      <el-alert v-if="topic.distinguishExpert" class="expert-tip" type="warning" :closable="false" show-icon>
        专家二维码仅供专家评委使用，请避免将专家评分链接公开传播。
      </el-alert>
    </div>

    <template #footer>
      <el-button @click="visible = false"> 关闭 </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

import QRCode from 'qrcode'

import { CopyDocument } from '@element-plus/icons-vue'

import { ElMessage } from 'element-plus'

import type { RatingTopic } from '@/types'

import { getExpertRatingUrl, getPublicRatingUrl } from '@/utils/ratingUrl'

/**
 * Dialog 显示状态。
 */
const visible = defineModel<boolean>({
  default: false,
})

/**
 * 当前评分主题。
 *
 * 二维码现在属于 RatingTopic，
 * 不再属于某个 RatingItem。
 */
const props = defineProps<{
  topic: RatingTopic | null
}>()

/**
 * 二维码生成状态。
 */
const loading = ref(false)

/**
 * 大众评分地址。
 */
const publicUrl = ref('')

/**
 * 专家评分地址。
 */
const expertUrl = ref('')

/**
 * 大众二维码。
 */
const publicQrCode = ref('')

/**
 * 专家二维码。
 */
const expertQrCode = ref('')

/**
 * 生成当前 Topic 对应的二维码。
 *
 * 二维码永久指向 Topic。
 *
 * 用户扫码后，由后端根据 Topic
 * 自动定位当前 status=1 的 RatingItem。
 */
async function generateQrCodes() {
  const topic = props.topic

  if (!topic) {
    return
  }

  loading.value = true

  try {
    /**
     * 大众评分地址。
     */
    publicUrl.value = getPublicRatingUrl(topic.id)

    publicQrCode.value = await QRCode.toDataURL(publicUrl.value, {
      width: 280,
      margin: 2,
      errorCorrectionLevel: 'M',
    })

    /**
     * 开启专家评分时，
     * 再生成专家评分二维码。
     */
    if (topic.distinguishExpert) {
      if (!topic.expertToken) {
        expertUrl.value = ''
        expertQrCode.value = ''

        ElMessage.warning('当前评分主题缺少专家评分凭证')

        return
      }

      expertUrl.value = getExpertRatingUrl(topic.id, topic.expertToken)

      expertQrCode.value = await QRCode.toDataURL(expertUrl.value, {
        width: 280,
        margin: 2,
        errorCorrectionLevel: 'M',
      })
    } else {
      expertUrl.value = ''
      expertQrCode.value = ''
    }
  } catch (error) {
    console.error('生成评分二维码失败：', error)

    ElMessage.error('二维码生成失败')
  } finally {
    loading.value = false
  }
}

/**
 * 复制评分地址。
 */
async function handleCopy(value: string) {
  if (!value) {
    return
  }

  try {
    await navigator.clipboard.writeText(value)

    ElMessage.success('链接已复制')
  } catch {
    ElMessage.error('复制失败，请手动复制链接')
  }
}

/**
 * Dialog 关闭后清理数据。
 */
function handleClosed() {
  publicUrl.value = ''
  expertUrl.value = ''

  publicQrCode.value = ''
  expertQrCode.value = ''
}

/**
 * Dialog 打开或者 Topic 发生变化时，
 * 重新生成二维码。
 */
watch([visible, () => props.topic], ([newVisible, topic]) => {
  if (newVisible && topic) {
    generateQrCodes()
  }
})
</script>

<style scoped>
.qr-dialog {
  min-height: 380px;
}

/* =========================
   Topic 信息
========================= */

.topic-info {
  margin-bottom: 24px;
  padding-bottom: 20px;

  border-bottom: 1px solid #ebeef5;
}

.topic-name {
  color: #303133;

  font-size: 18px;
  font-weight: 600;
}

.topic-description {
  margin-top: 8px;

  color: #909399;

  font-size: 13px;
  line-height: 20px;
}

/* =========================
   二维码布局
========================= */

.qr-list {
  display: grid;

  grid-template-columns: repeat(2, minmax(0, 1fr));

  gap: 24px;
}

.qr-list-single {
  grid-template-columns: minmax(0, 340px);

  justify-content: center;
}

/* =========================
   二维码卡片
========================= */

.qr-card {
  display: flex;
  flex-direction: column;
  align-items: center;

  padding: 20px;

  border: 1px solid #ebeef5;
  border-radius: 8px;

  background: #ffffff;

  box-sizing: border-box;
}

.qr-card-header {
  width: 100%;

  display: flex;
  align-items: center;
  justify-content: space-between;

  margin-bottom: 18px;
}

.qr-card-title {
  color: #303133;

  font-size: 16px;
  font-weight: 500;
}

/* =========================
   二维码图片
========================= */

.qr-image-wrapper {
  width: 240px;
  height: 240px;

  display: flex;
  align-items: center;
  justify-content: center;

  background: #ffffff;
}

.qr-image {
  width: 240px;
  height: 240px;

  display: block;
}

/* =========================
   链接
========================= */

.qr-url {
  width: 100%;

  margin-top: 16px;

  overflow: hidden;

  color: #909399;

  font-size: 12px;
  line-height: 18px;

  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-button {
  margin-top: 14px;
}

/* =========================
   专家提示
========================= */

.expert-tip {
  margin-top: 24px;
}
</style>
