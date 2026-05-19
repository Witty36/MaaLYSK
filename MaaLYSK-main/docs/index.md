 <!-- markdownlint-disable MD022 MD041-->
---
layout: false
---

<script setup>
import { onMounted } from 'vue'
import { withBase } from 'vitepress'

onMounted(() => {
  window.location.replace(withBase('/zh_cn/'))
})
</script>
