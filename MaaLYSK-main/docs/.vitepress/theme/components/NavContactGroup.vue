<script lang="ts" setup>
import { computed } from 'vue'
import { useData } from 'vitepress'

const { lang } = useData()
const label = computed(() => lang.value === 'zh-CN' ? '联系我们' : 'Contact Us')

const githubRepoLink = 'https://github.com/Witty36/MaaLYSK'
const qqGroupLink =
    'https://qm.qq.com/cgi-bin/qm/qr?k=74p64gDsFVQD0q7VY4yI6dgBo7p6H9GG&jump_from=webapi&authKey=/cejhv0J4X5LQ6cg+emj87fWIcNOSTL5gWBnn2VD4I0cw0ciNd3LxL1++sqUkl4a'
const qqIconSvg =
    '<svg viewBox="0 0 1024 1024" aria-hidden="true"><path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 689.3 112 511.5 112 331.7 112 256.2 265.2 261 447.9c-28.4 70.8-46.7 113.6-62.7 165.3-34 109.5-23 154.8-14.6 155.8 18 2.2 70.1-82.4 70.1-82.4 0 49 25.2 112.9 79.8 159-26.4 8.1-85.7 29.9-71.6 53.8 11.4 19.3 196.2 12.3 249.5 6.3 53.3 6 238.1 13 249.5-6.3 14.1-23.8-45.3-45.7-71.6-53.8 54.6-46.2 79.8-110.1 79.8-159 0 0 52.1 84.6 70.1 82.4 8.5-1.1 19.5-46.4-14.5-155.8z" fill="currentColor"></path></svg>'
</script>

<template>
  <span class="nav-contact-group">
    <span class="nav-contact-divider"></span>
    <span class="nav-contact-label">{{ label }}</span>
    <a
      class="nav-contact-icon"
      :href="qqGroupLink"
      target="_blank"
      rel="noopener"
      title="QQ群"
      v-html="qqIconSvg"
    ></a>
    <a
      class="nav-contact-icon"
      :href="githubRepoLink"
      target="_blank"
      rel="noopener"
      title="GitHub"
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" fill="currentColor" />
      </svg>
    </a>
  </span>
</template>
