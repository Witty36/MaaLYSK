<template>
  <div class="flowchart" ref="chartRef"></div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  code: { type: String, required: true }
})

const chartRef = ref(null)

onMounted(async () => {
  const mermaid = (await import('mermaid')).default
  mermaid.initialize({ startOnLoad: false, theme: 'default' })
  const id = 'flowchart-' + Math.random().toString(36).slice(2, 10)
  const { svg } = await mermaid.render(id, props.code.trim())
  if (chartRef.value) {
    chartRef.value.innerHTML = svg
  }
})
</script>

<style scoped>
.flowchart {
  display: flex;
  justify-content: center;
  margin: 1em 0;
  overflow-x: auto;
}
.flowchart :deep(svg) {
  max-width: 100%;
  height: auto;
}
</style>
