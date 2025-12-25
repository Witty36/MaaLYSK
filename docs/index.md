---
layout: false
---

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vitepress'

const router = useRouter()

onMounted(() => {
  // 访问根目录时，自动跳转到 zh_cn
  // 使用 window.location 确保跳转最稳健
  const basePath = '/MaaLYSK'
  window.location.href = `${basePath}/zh_cn/`
})
</script>
