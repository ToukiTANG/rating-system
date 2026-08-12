<template>
  <el-dialog
    :model-value="modelValue"
    title="新增评分项目"
    width="600px"
    :close-on-click-modal="false"
    :close-on-press-escape="!submitting"
    :show-close="!submitting"
    @update:model-value="handleVisibleChange"
    @closed="handleClosed"
  >
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="90px">
      <el-form-item label="项目名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入项目名称"
          maxlength="50"
          show-word-limit
          clearable
        />
      </el-form-item>

      <el-form-item label="项目描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          placeholder="请输入项目描述"
          :rows="4"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button :disabled="submitting" @click="handleCancel"> 取消 </el-button>

        <el-button type="primary" :loading="submitting" @click="handleSubmit"> 确定 </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

import { createRatingItem } from '@/api/rating/rating'

interface Props {
  modelValue: boolean
}

interface AddRatingItemForm {
  name: string
  description: string
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'success'): void
}>()

const formRef = ref<FormInstance>()

const submitting = ref(false)

const formData = reactive<AddRatingItemForm>({
  name: '',
  description: '',
})

const formRules: FormRules<AddRatingItemForm> = {
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
      max: 500,
      message: '项目描述长度不能超过 500 个字符',
      trigger: 'blur',
    },
  ],
}

/**
 * Dialog 显示状态变化
 */
function handleVisibleChange(value: boolean) {
  if (submitting.value) {
    return
  }

  emit('update:modelValue', value)
}

/**
 * 取消
 */
function handleCancel() {
  if (submitting.value) {
    return
  }

  emit('update:modelValue', false)
}

/**
 * 提交
 */
async function handleSubmit() {
  if (!formRef.value || submitting.value) {
    return
  }

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true

  try {
    await createRatingItem({
      name: formData.name.trim(),
      description: formData.description.trim(),
    })

    ElMessage.success('新增成功')

    emit('update:modelValue', false)

    emit('success')
  } catch {
    // 异常提示已经由 request.ts 统一处理
    // 这里不重复 ElMessage.error
  } finally {
    submitting.value = false
  }
}

/**
 * Dialog 完全关闭后重置表单
 */
function handleClosed() {
  formRef.value?.resetFields()

  formData.name = ''
  formData.description = ''
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
