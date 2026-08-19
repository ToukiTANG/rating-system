<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="520px"
    :close-on-click-modal="false"
    :close-on-press-escape="!busy"
    :show-close="!busy"
    @closed="handleClosed"
  >
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
      <!-- 所属评分主题 -->
      <el-form-item label="评分主题" prop="topicId" required>
        <el-select v-model="formData.topicId" placeholder="请选择评分主题" filterable style="width: 100%" :loading="topicLoading" :disabled="isEdit">
          <el-option v-for="topic in topicList" :key="topic.id" :label="topic.name" :value="topic.id" />
        </el-select>

        <div v-if="isEdit" class="field-tip">评分项目创建后不可修改所属主题</div>
      </el-form-item>

      <!-- 项目名称 -->
      <el-form-item label="项目名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入项目名称" maxlength="50" show-word-limit clearable />
      </el-form-item>

      <!-- 项目图片 -->
      <el-form-item label="项目图片" prop="imageUrl" required>
        <!-- 编辑模式：仅展示 -->
        <template v-if="isEdit">
          <div class="image-field">
            <el-image
              v-if="formData.imageUrl"
              :src="formData.imageUrl"
              :preview-src-list="[formData.imageUrl]"
              fit="cover"
              class="item-image-preview"
              preview-teleported
            />

            <div v-else class="image-empty">暂无图片</div>

            <div class="field-tip">评分项目创建后暂不支持修改图片</div>
          </div>
        </template>

        <!-- 新增模式：允许上传 -->
        <template v-else>
          <div class="image-field">
            <el-upload
              class="item-image-uploader"
              :show-file-list="false"
              :http-request="handleImageUpload"
              :before-upload="handleBeforeImageUpload"
              accept="image/jpeg,image/png,image/webp"
              :disabled="imageUploading"
            >
              <!-- 已上传 -->
              <div v-if="formData.imageUrl" class="upload-image-wrapper">
                <img :src="formData.imageUrl" class="upload-image" alt="项目图片" />

                <div class="upload-image-mask">重新上传</div>
              </div>

              <!-- 未上传 -->
              <div v-else class="image-upload-placeholder">
                <el-icon v-if="!imageUploading" class="upload-icon">
                  <Plus />
                </el-icon>

                <span>
                  {{ imageUploading ? '上传中...' : '上传图片' }}
                </span>
              </div>
            </el-upload>

            <div class="field-tip">支持 JPG、PNG、WEBP，图片大小不超过 5 MB</div>
          </div>
        </template>
      </el-form-item>

      <!-- 项目描述 -->
      <el-form-item label="项目描述" prop="description">
        <el-input v-model="formData.description" type="textarea" placeholder="请输入项目描述" :rows="4" maxlength="500" show-word-limit />
      </el-form-item>
    </el-form>

    <!-- 底部操作区域 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button :disabled="busy" @click="handleCancel"> 取消 </el-button>

        <el-button type="primary" :loading="submitting" :disabled="imageUploading" @click="handleSubmit">
          {{ isEdit ? '保存' : '新增' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'

import { ElMessage, type FormInstance, type FormRules, type UploadRawFile, type UploadRequestOptions } from 'element-plus'

import { createRatingItem, updateRatingItem, uploadItemImage } from '@/api/rating/rating.ts'

import { queryRatingTopic } from '@/api/rating/RatingTopic.ts'

import type { RatingTopic, RatingItem } from '@/types'

import { Plus } from '@element-plus/icons-vue'

/**
 * 弹窗显示状态。
 *
 * 父组件可以直接使用：
 *
 * <AddOrUpdate v-model="dialogVisible" />
 */
const visible = defineModel<boolean>({
  default: false,
})

/**
 * 父组件传入的数据。
 *
 * item = null：
 *   新增模式
 *
 * item != null：
 *   编辑模式
 */
const props = defineProps<{
  item?: RatingItem | null
}>()

/**
 * 弹窗操作成功事件。
 *
 * mode：
 *   add  - 新增成功
 *   edit - 编辑成功
 */
const emit = defineEmits<{
  (e: 'success', mode: 'add' | 'edit'): void
}>()

/**
 * 表单数据。
 *
 * RatingItem 的专家配置已经迁移到 RatingTopic，
 * 因此当前表单只维护：
 *
 * - topicId
 * - name
 * - description
 */
interface RatingItemForm {
  topicId: number | null
  name: string
  description: string

  /**
   * 项目图片 CDN 地址。
   */
  imageUrl: string
}

const formRef = ref<FormInstance>()

const submitting = ref(false)

/**
 * 图片上传状态。
 */
const imageUploading = ref(false)

/**
 * 当前弹窗是否正在执行不可中断操作。
 */
const busy = computed(() => {
  return submitting.value || imageUploading.value
})

const topicLoading = ref(false)

const topicList = ref<RatingTopic[]>([])

const formData = reactive<RatingItemForm>({
  topicId: null,
  name: '',
  description: '',
  imageUrl: '',
})

/**
 * 当前是否为编辑模式。
 */
const isEdit = computed(() => {
  return props.item?.id != null
})

/**
 * 根据当前模式动态设置弹窗标题。
 */
const dialogTitle = computed(() => {
  return isEdit.value ? '编辑评分项目' : '新增评分项目'
})

/**
 * 表单校验规则。
 */
const formRules: FormRules<RatingItemForm> = {
  topicId: [
    {
      validator: (_rule, value, callback) => {
        /**
         * 编辑模式下所属 Topic 不允许修改，
         * 并且 Update API 不需要 topicId，
         * 因此无需再次校验。
         */
        if (isEdit.value) {
          callback()
          return
        }

        if (value == null) {
          callback(new Error('请选择评分主题'))
          return
        }

        callback()
      },
      trigger: 'change',
    },
  ],

  name: [
    {
      required: true,
      message: '请输入项目名称',
      trigger: 'blur',
    },
    {
      min: 1,
      max: 50,
      message: '项目名称长度不能超过 50 个字符',
      trigger: 'blur',
    },
  ],

  description: [
    {
      required: true,
      message: '请输入项目描述',
      trigger: 'blur',
    },
    {
      max: 500,
      message: '项目描述长度不能超过 500 个字符',
      trigger: 'blur',
    },
  ],
  imageUrl: [
    {
      validator: (_rule, value, callback) => {
        /**
         * 编辑模式不允许修改图片，
         * 因此不要求历史数据必须存在图片。
         */
        if (isEdit.value) {
          callback()
          return
        }

        if (typeof value !== 'string' || !value.trim()) {
          callback(new Error('请上传项目图片'))
          return
        }

        callback()
      },
      trigger: 'change',
    },
  ],
}

/**
 * 加载评分主题。
 *
 * 当前用于 RatingItem 新增时选择所属 Topic，
 * 以及编辑时展示当前 Topic。
 */
async function loadTopics() {
  topicLoading.value = true

  try {
    const response = await queryRatingTopic({
      page: 1,
      pageSize: 100,
    })

    topicList.value = response.list
  } finally {
    topicLoading.value = false
  }
}

/**
 * 初始化弹窗表单。
 *
 * 新增模式：
 *   清空表单。
 *
 * 编辑模式：
 *   将父组件传入的 item 数据复制到本地表单。
 */
async function initForm() {
  /**
   * 先加载 Topic，
   * 保证 Select 能正确展示 Topic 名称。
   */
  await loadTopics()

  if (isEdit.value && props.item) {
    formData.topicId = props.item.topicId

    formData.name = props.item.name

    formData.description = props.item.description ?? ''

    formData.imageUrl = props.item.imageUrl ?? ''
  } else {
    formData.topicId = null
    formData.name = ''
    formData.description = ''
    formData.imageUrl = ''
  }

  /**
   * 等待 DOM 和 Form 状态更新完成后，
   * 清除上一次打开弹窗留下的校验信息。
   */
  await nextTick(() => {
    formRef.value?.clearValidate()
  })
}

/**
 * 上传前校验图片。
 *
 * 后端仍会再次校验，
 * 这里主要用于提前给用户反馈。
 */
function handleBeforeImageUpload(file: UploadRawFile): boolean {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']

  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 JPG、PNG、WEBP 图片')

    return false
  }

  const maxSize = 5 * 1024 * 1024

  if (file.size > maxSize) {
    ElMessage.error('图片大小不能超过 5 MB')

    return false
  }

  return true
}

/**
 * 上传 RatingItem 图片。
 *
 * 上传成功后，后端返回又拍云 CDN URL，
 * 表单最终只保存这个 URL。
 */
async function handleImageUpload(options: UploadRequestOptions) {
  imageUploading.value = true

  try {
    const result = await uploadItemImage(options.file)

    formData.imageUrl = result.url

    /**
     * 图片已经上传成功，
     * 清除 imageUrl 的表单错误状态。
     */
    await nextTick()

    formRef.value?.clearValidate('imageUrl')

    ElMessage.success('图片上传成功')
  } finally {
    imageUploading.value = false
  }
}

/**
 * 每次打开弹窗时重新初始化表单。
 */
watch(
  () => visible.value,
  (newVisible) => {
    if (newVisible) {
      initForm()
    }
  },
)

/**
 * 弹窗打开过程中父组件切换 item 时，
 * 同步更新表单。
 */
watch(
  () => props.item,
  () => {
    if (visible.value) {
      initForm()
    }
  },
)

/**
 * 取消操作。
 */
function handleCancel() {
  if (submitting.value) {
    return
  }

  visible.value = false
}

/**
 * 提交新增 / 修改表单。
 */
async function handleSubmit() {
  if (!formRef.value || submitting.value) {
    return
  }

  /**
   * 先执行表单校验。
   */
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true

  try {
    if (isEdit.value) {
      await submitUpdate()
    } else {
      await submitAdd()
    }

    /**
     * 操作成功后关闭弹窗。
     */
    visible.value = false
  } catch {
    /**
     * HTTP / 业务异常已经由 request.ts
     * 统一处理，这里不重复弹出错误提示。
     */
  } finally {
    submitting.value = false
  }
}

/**
 * 新增 RatingItem。
 *
 * 新增时必须指定所属 Topic。
 */
async function submitAdd() {
  const topicId = formData.topicId

  if (topicId == null) {
    return
  }

  const imageUrl = formData.imageUrl.trim()

  if (!imageUrl) {
    return
  }

  await createRatingItem({
    topicId,
    name: formData.name.trim(),
    description: formData.description.trim(),
    imageUrl,
  })

  ElMessage.success('新增成功')

  emit('success', 'add')
}

/**
 * 修改 RatingItem。
 *
 * RatingItem 创建后不允许修改所属 Topic，
 * 因此 Update API 不发送 topicId。
 */
async function submitUpdate() {
  const id = props.item?.id

  if (id == null) {
    return
  }

  await updateRatingItem({
    id,
    name: formData.name.trim(),
    description: formData.description.trim(),
  })

  ElMessage.success('修改成功')

  emit('success', 'edit')
}

/**
 * Dialog 完全关闭后清理本地状态。
 */
function handleClosed() {
  formData.topicId = null
  formData.name = ''
  formData.description = ''
  formData.imageUrl = ''

  imageUploading.value = false

  formRef.value?.clearValidate()
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.field-tip {
  width: 100%;
  margin-top: 4px;

  font-size: 12px;
  line-height: 18px;

  color: #909399;
}

/* =========================
   项目图片
========================= */

.image-field {
  width: 100%;
}

.item-image-uploader {
  width: 160px;
}

.item-image-uploader :deep(.el-upload) {
  width: 160px;
  height: 120px;

  overflow: hidden;

  border: 1px dashed #dcdfe6;
  border-radius: 8px;

  background: #fafafa;

  transition:
    border-color 0.2s ease,
    background-color 0.2s ease;
}

.item-image-uploader :deep(.el-upload:hover) {
  border-color: var(--el-color-primary);

  background: #f5f7fa;
}

/* 未上传状态 */
.image-upload-placeholder {
  width: 100%;
  height: 100%;

  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  gap: 8px;

  color: #909399;

  font-size: 13px;
}

.upload-icon {
  color: #909399;

  font-size: 28px;
}

/* 上传后的图片 */
.upload-image-wrapper {
  position: relative;

  width: 100%;
  height: 100%;

  overflow: hidden;
}

.upload-image {
  width: 100%;
  height: 100%;

  display: block;

  object-fit: cover;
}

.upload-image-mask {
  position: absolute;
  inset: 0;

  display: flex;
  align-items: center;
  justify-content: center;

  background: rgb(0 0 0 / 45%);

  color: #ffffff;

  font-size: 14px;

  opacity: 0;

  transition: opacity 0.2s ease;
}

.upload-image-wrapper:hover .upload-image-mask {
  opacity: 1;
}

/* 编辑状态图片 */
.item-image-preview {
  width: 160px;
  height: 120px;

  display: block;

  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

/* 历史无图片数据 */
.image-empty {
  width: 160px;
  height: 120px;

  display: flex;
  align-items: center;
  justify-content: center;

  border: 1px dashed #dcdfe6;
  border-radius: 8px;

  background: #fafafa;

  color: #909399;

  font-size: 13px;
}
</style>
