<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="520px"
    :close-on-click-modal="false"
    :close-on-press-escape="!submitting"
    :show-close="!submitting"
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

      <!-- 项目描述 -->
      <el-form-item label="项目描述" prop="description">
        <el-input v-model="formData.description" type="textarea" placeholder="请输入项目描述" :rows="4" maxlength="500" show-word-limit />
      </el-form-item>
    </el-form>

    <!-- 底部操作区域 -->
    <template #footer>
      <div class="dialog-footer">
        <el-button :disabled="submitting" @click="handleCancel"> 取消 </el-button>

        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保存' : '新增' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from 'vue'

import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import { createRatingItem, updateRatingItem } from '@/api/rating/rating.ts'

import { queryRatingTopic } from '@/api/rating/RatingTopic.ts'

import type { RatingTopic, RatingItem } from '@/types'

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
}

const formRef = ref<FormInstance>()

const submitting = ref(false)

const topicLoading = ref(false)

const topicList = ref<RatingTopic[]>([])

const formData = reactive<RatingItemForm>({
  topicId: null,
  name: '',
  description: '',
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
  } else {
    formData.topicId = null
    formData.name = ''
    formData.description = ''
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

  await createRatingItem({
    topicId,
    name: formData.name.trim(),
    description: formData.description.trim(),
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
</style>
