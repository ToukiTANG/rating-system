<template>
  <el-dialog v-model="visible" :title="title" width="560px" destroy-on-close @closed="handleClosed">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
      <el-form-item label="主题名称" prop="name">
        <el-input v-model="form.name" maxlength="50" placeholder="请输入评分主题名称" />
      </el-form-item>

      <el-form-item label="主题描述" prop="description">
        <el-input v-model="form.description" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="请输入评分主题描述" />
      </el-form-item>

      <el-form-item label="区分专家" prop="distinguishExpert" required>
        <el-switch v-model="form.distinguishExpert" :disabled="isEdit" @change="handleExpertChange" />

        <span v-if="isEdit" class="field-tip"> 创建后不可修改 </span>
      </el-form-item>

      <el-form-item label="大众评委人数" prop="publicLimit" required>
        <el-input-number v-model="form.publicLimit" :min="1" :step="1" :precision="0" :disabled="isEdit" controls-position="right" style="width: 180px" />

        <span v-if="isEdit" class="field-tip"> 创建后不可修改 </span>
      </el-form-item>

      <template v-if="showExpertConfig">
        <el-form-item label="专家评委人数" prop="expertLimit" required>
          <el-input-number v-model="form.expertLimit" :min="1" :step="1" :precision="0" :disabled="isEdit" controls-position="right" style="width: 180px" />

          <span v-if="isEdit" class="field-tip"> 创建后不可修改 </span>
        </el-form-item>

        <el-form-item label="专家评分占比" prop="expertWeight" required>
          <el-input-number v-model="form.expertWeight" :min="1" :max="99" :step="1" :precision="0" controls-position="right" style="width: 180px" />

          <span class="weight-unit"> % </span>
        </el-form-item>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="visible = false"> 取消 </el-button>

      <el-button type="primary" :loading="submitting" @click="handleSubmit"> 确定 </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { ElMessage, type FormInstance, type FormRules } from 'element-plus'

import { addRatingTopic, updateRatingTopic } from '@/api/rating/RatingTopic.ts'

import type { RatingTopic, RatingTopicCreateRequest, RatingTopicUpdateRequest } from '@/types'

const emit = defineEmits<{
  success: []
}>()

const visible = ref(false)

const submitting = ref(false)

const formRef = ref<FormInstance>()

/**
 * 当前编辑的数据。
 *
 * null：
 *   新增模式
 *
 * 非 null：
 *   编辑模式
 */
const currentTopic = ref<RatingTopic | null>(null)

interface TopicForm {
  name: string
  description: string
  distinguishExpert: boolean
  expertWeight: number | null
  publicLimit: number
  expertLimit: number | null
}

const form = reactive<TopicForm>({
  name: '',
  description: '',
  distinguishExpert: false,
  expertWeight: null,
  publicLimit: 1,
  expertLimit: null,
})

/**
 * 是否为编辑模式。
 */
const isEdit = computed(() => currentTopic.value !== null)

const title = computed(() => (isEdit.value ? '编辑评分主题' : '新增评分主题'))

/**
 * 是否显示专家相关配置。
 *
 * 编辑模式下 distinguishExpert 不允许修改，
 * 因此这里仍然可以直接读取 form 中的值。
 */
const showExpertConfig = computed(() => form.distinguishExpert)

const rules: FormRules<TopicForm> = {
  name: [
    {
      required: true,
      message: '请输入评分主题名称',
      trigger: 'blur',
    },
    {
      min: 1,
      max: 50,
      message: '评分主题名称长度不能超过 50 个字符',
      trigger: 'blur',
    },
  ],

  description: [
    {
      max: 500,
      message: '评分主题描述不能超过 500 个字符',
      trigger: 'blur',
    },
  ],

  publicLimit: [
    {
      required: true,
      message: '请输入大众评委人数',
      trigger: 'change',
    },
  ],

  expertWeight: [
    {
      validator: (_rule, value, callback) => {
        if (!form.distinguishExpert) {
          callback()
          return
        }

        if (value == null) {
          callback(new Error('请输入专家评分占比'))
          return
        }

        if (value <= 0 || value >= 100) {
          callback(new Error('专家评分占比必须大于 0 且小于 100'))
          return
        }

        callback()
      },
      trigger: 'change',
    },
  ],

  expertLimit: [
    {
      validator: (_rule, value, callback) => {
        if (!form.distinguishExpert) {
          callback()
          return
        }

        if (value == null || value < 1) {
          callback(new Error('请输入专家评委人数'))
          return
        }

        callback()
      },
      trigger: 'change',
    },
  ],
}

/**
 * 清空表单。
 */
function resetForm() {
  currentTopic.value = null

  form.name = ''
  form.description = ''
  form.distinguishExpert = false
  form.expertWeight = null
  form.publicLimit = 1
  form.expertLimit = null

  formRef.value?.clearValidate()
}

/**
 * 打开新增弹窗。
 */
function openAdd() {
  resetForm()

  visible.value = true
}

/**
 * 打开编辑弹窗。
 */
function openUpdate(topic: RatingTopic) {
  currentTopic.value = topic

  form.name = topic.name
  form.description = topic.description

  form.distinguishExpert = topic.distinguishExpert

  form.expertWeight = topic.expertWeight == null ? null : topic.expertWeight * 100

  form.publicLimit = topic.publicLimit

  form.expertLimit = topic.expertLimit

  formRef.value?.clearValidate()

  visible.value = true
}

/**
 * 是否区分专家发生变化。
 *
 * 只有新增模式可以切换。
 */
function handleExpertChange(value: boolean) {
  if (value) {
    // 默认给一个比较直观的专家占比。
    if (form.expertWeight == null) {
      form.expertWeight = 60
    }

    if (form.expertLimit == null) {
      form.expertLimit = 1
    }

    return
  }

  form.expertWeight = null
  form.expertLimit = null
}

/**
 * 提交。
 */
async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  const valid = await formRef.value.validate().catch(() => false)

  if (!valid) {
    return
  }

  submitting.value = true

  try {
    if (isEdit.value) {
      await submitUpdate()
    } else {
      await submitAdd()
    }

    visible.value = false

    ElMessage.success(isEdit.value ? '修改成功' : '新增成功')

    emit('success')
  } finally {
    submitting.value = false
  }
}

/**
 * 新增 Topic。
 */
async function submitAdd() {
  const request: RatingTopicCreateRequest = {
    name: form.name.trim(),

    description: form.description.trim(),

    distinguishExpert: form.distinguishExpert,

    /**
     * 前端输入使用百分数：
     *
     * 60
     *
     * 后端存储使用：
     *
     * 0.6
     */
    expertWeight: form.distinguishExpert && form.expertWeight != null ? form.expertWeight / 100 : null,

    publicLimit: form.publicLimit,

    expertLimit: form.distinguishExpert ? form.expertLimit : null,
  }

  await addRatingTopic(request)
}

/**
 * 修改 Topic。
 *
 * 后端 Update API 只接受：
 *
 * id
 * name
 * description
 * expertWeight
 *
 * 不允许修改人数和是否区分专家。
 */
async function submitUpdate() {
  const topic = currentTopic.value

  if (!topic) {
    return
  }

  const request: RatingTopicUpdateRequest = {
    id: topic.id,

    name: form.name.trim(),

    description: form.description.trim(),

    expertWeight: topic.distinguishExpert && form.expertWeight != null ? form.expertWeight / 100 : null,
  }

  await updateRatingTopic(request)
}

function handleClosed() {
  resetForm()
}

defineExpose({
  openAdd,
  openUpdate,
})
</script>

<style scoped>
.field-tip {
  margin-left: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.weight-unit {
  margin-left: 8px;
  color: var(--el-text-color-regular);
}
</style>
