<template>
  <div class="rating-view">
    <!--
      RatingView 独立评分页面。

      后续评分业务 UI 在这里实现。
    -->
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

/**
 * 当前评分项目 ID。
 *
 * URL 示例：
 * /rating/12
 *
 * 则 ratingItemId = 12。
 */
const ratingItemId = computed(() => {
  return Number(route.params.id)
})
</script>

<style scoped>
.rating-view {
  width: 100%;
  height: 100vh;

  overflow: hidden;

  box-sizing: border-box;

  background: #f5f6f8;
}
</style>
