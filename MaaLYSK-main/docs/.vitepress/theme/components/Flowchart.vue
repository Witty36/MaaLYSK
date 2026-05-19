<template>
  <div class="flowchart"></div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import mermaid from 'mermaid'

const props = defineProps<{
  code: string
}>()

onMounted(async () => {
  console.log('Flowchart mounting, code:', props.code)
  
  mermaid.initialize({
    startOnLoad: false,
    theme: 'default',
    securityLevel: 'loose'
  })
  
  try {
    const id = `mermaid-${Date.now()}`
    const { svg } = await mermaid.render(id, props.code)
    const container = document.querySelector('.flowchart')
    if (container) {
      container.innerHTML = svg
    }
    console.log('Render success')
  } catch (err) {
    console.error('Render error:', err)
  }
})
</script>