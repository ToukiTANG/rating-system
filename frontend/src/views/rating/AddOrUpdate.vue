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
      <!-- 项目名称 -->
      <el-form-item label="项目名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入项目名称" maxlength="50" show-word-limit clearable />
      </el-form-item>

      <!-- 项目描述 -->
      <el-form-item label="项目描述" prop="description">
        <el-input v-model="formData.description" type="textarea" placeholder="请输入项目描述" :rows="4" maxlength="500" show-word-limit />
      </el-form-item>

      <!-- 项目描述 -->
      <el-form-item label="区分专家评委" prop="distinguishExpert">
        <el-switch v-model="formData.distinguishExpert" active-text="是" inactive-text="否" />
      </el-form-item>
      <el-form-item v-if="formData.distinguishExpert" label="专家评分占比" prop="expertWeight" required>
        <el-input-number v-model="formData.expertWeight" :min="1" :max="99" :step="5" :precision="0" />
        <span class="unit"> % </span>
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

import { createRatingItem, updateRatingItem } from '@/api/rating/rating'
import type { RatingItem } from '@/types'

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
 *
 * item：
 *   后端返回的最新评分项目数据
 */
const emit = defineEmits<{
  (e: 'success', mode: 'add' | 'edit'): void
}>()

/**
 * 表单数据。
 *
 * 不直接修改 props.item，
 * 避免编辑过程中直接影响父组件表格中的原始数据。
 */
interface RatingItemForm {
  name: string
  description: string
  distinguishExpert: boolean
  expertWeight: number | null
}

const formRef = ref<FormInstance>()

const submitting = ref(false)

const formData = reactive<RatingItemForm>({
  name: '',
  description: '',
  distinguishExpert: false,
  expertWeight: 60,
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
      max: 500,
      message: '项目描述长度不能超过 500 个字符',
      trigger: 'blur',
    },
  ],

  distinguishExpert: [
    {
      required: true,
      trigger: 'change',
      message: '请选择是否需要区分专家评委',
    },
  ],
  expertWeight: [
    {
      validator: (_rule, value, callback) => {
        /**
         * 不区分专家评委时，
         * 不需要校验专家评分占比。
         */
        if (!formData.distinguishExpert) {
          callback()
          return
        }

        /**
         * 区分专家评委时，
         * 专家评分占比必须填写。
         */
        if (value === null || value === undefined || value === '') {
          callback(new Error('请输入专家评分占比'))
          return
        }

        /**
         * 专家评分占比必须在 0% ～ 100% 之间，
         * 且不能取边界值。
         */
        if (Number(value) <= 0 || Number(value) >= 100) {
          callback(new Error('专家评分占比必须大于 0% 且小于 100%'))
          return
        }

        callback()
      },
      trigger: ['blur', 'change'],
    },
  ],
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
function initForm() {
  if (isEdit.value && props.item) {
    formData.name = props.item.name
    formData.description = props.item.description ?? ''
  } else {
    formData.name = ''
    formData.description = ''
  }

  /**
   * 等待 DOM 和 Form 状态更新完成后，
   * 清除上一次打开弹窗留下的校验信息。
   */
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

/**
 * 每次打开弹窗时重新初始化表单。
 *
 * 这样可以保证：
 *
 * 第一次新增
 *     ↓
 * 关闭
 *     ↓
 * 再次编辑
 *
 * 时不会残留上一次的数据。
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
 * 当弹窗已经打开，但父组件切换了 item 时，
 * 同步更新表单数据。
 *
 * 正常情况下很少触发，
 * 但可以让组件行为更加完整。
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
 * 提交表单。
 */
/**
 * 提交新增 / 修改表单
 */
async function handleSubmit() {
  if (!formRef.value || submitting.value) {
    return
  }

  // 先执行表单校验
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true

  try {
    if (isEdit.value) {
      /**
       * 修改模式
       */
      const id = props.item?.id
      // 提交前统一去除字符串首尾空格
      const requestData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        distinguishExpert: formData.distinguishExpert,
        expertWeight: formData.distinguishExpert && formData.expertWeight !== null ? formData.expertWeight / 100 : null,
      }

      if (id == null) {
        return
      }

      await updateRatingItem({
        id,
        ...requestData,
      })

      ElMessage.success('修改成功')

      emit('success', 'edit')
    } else {
      /**
       * 新增模式
       */
      // 提交前统一去除字符串首尾空格
      const requestData = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        distinguishExpert: formData.distinguishExpert,
        expertWeight: formData.distinguishExpert && formData.expertWeight !== null ? formData.expertWeight / 100 : null,
      }
      await createRatingItem(requestData)

      ElMessage.success('新增成功')

      emit('success', 'add')
    }

    // 操作成功后关闭弹窗
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
 * Dialog 完全关闭后清理本地状态。
 */
function handleClosed() {
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
</style>
