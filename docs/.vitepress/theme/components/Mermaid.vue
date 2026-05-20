<template>
  <div ref="container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import mermaid from 'mermaid'

const container = ref<HTMLDivElement>()

onMounted(async () => {
  console.log('Mermaid mounted')
  
  // 直接获取 <Mermaid> 标签内的原始 HTML 内容
  const parent = container.value?.parentElement
  if (!parent) {
    console.error('No parent element')
    return
  }
  
  // 获取原始内容并提取代码
  const html = parent.innerHTML
  const match = html.match(/<Mermaid>([\s\S]*?)<\/Mermaid>/)
  
  if (!match) {
    console.error('No mermaid code found')
    return
  }
  
  // 解码 HTML 实体并保留换行
  let code = match[1]
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .trim()
  
  console.log('Raw code:', code)
  
  if (!code) {
    console.error('Empty code')
    return
  }
  
  mermaid.initialize({
    startOnLoad: false,
    theme: 'default',
    securityLevel: 'loose'
  })
  
  try {
    const id = `mermaid-${Date.now()}`
    const { svg } = await mermaid.render(id, code)
    if (container.value) {
      container.value.innerHTML = svg
    }
    console.log('Render success')
  } catch (err) {
    console.error('Render error:', err)
    if (container.value) {
      container.value.innerHTML = `<pre style="color: red; background: #ffeeee; padding: 1em; white-space: pre-wrap;">渲染失败: ${err}\n\n代码内容:\n${code}</pre>`
    }
  }
})
</script>