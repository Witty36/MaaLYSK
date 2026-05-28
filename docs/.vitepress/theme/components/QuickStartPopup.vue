<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vitepress'

const router = useRouter()

const visible = ref(false)
const step = ref<'choice' | 'download'>('choice')

function show() {
  step.value = 'choice'
  visible.value = true
}

function dismiss() {
  visible.value = false
}

function goUpdate() {
  visible.value = false
  router.go('/zh_cn/manual/1.4')
}

function goSimple() {
  visible.value = false
  router.go('/zh_cn/manual/1.1')
}

function goDetailed() {
  visible.value = false
  router.go('/zh_cn/manual/1.3')
}

onMounted(() => {
  const handler = (e: Event) => {
    const target = e.target as Element
    const el = target.closest('a[href="#quick-start-popup"]')
    if (!el) return
    e.preventDefault()
    e.stopImmediatePropagation()
    show()
  }
  document.addEventListener('click', handler, true)
  document.addEventListener('mousedown', handler, true)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="vp-overlay" @click.self="dismiss">
      <div class="vp-dialog">
        <button class="vp-close" @click="dismiss" title="关闭">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>

        <template v-if="step === 'choice'">
          <div class="vp-body">
            <p class="vp-title">快速开始</p>
            <p class="vp-subtitle">请选择你需要进行的操作</p>
            <div class="vp-actions">
              <button class="vp-btn vp-btn-primary" @click="step = 'download'">
                <span class="vp-btn-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                </span>
                <span class="vp-btn-text">
                  <span class="vp-btn-title">我要下载</span>
                  <span class="vp-btn-desc">首次安装 MaaLYSK</span>
                </span>
              </button>
              <button class="vp-btn vp-btn-outline" @click="goUpdate()">
                <span class="vp-btn-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
                </span>
                <span class="vp-btn-text">
                  <span class="vp-btn-title">我要更新</span>
                  <span class="vp-btn-desc">已安装，升级到最新版</span>
                </span>
              </button>
            </div>
          </div>
        </template>

        <template v-if="step === 'download'">
          <div class="vp-body">
            <p class="vp-subtitle">请选择适合你的下载教程</p>
            <div class="vp-actions">
              <button class="vp-btn vp-btn-primary" @click="goSimple()">
                <span class="vp-btn-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 5 14 11 14 10 22 20 9 13 9 14 2"/></svg>
                </span>
                <span class="vp-btn-text">
                  <span class="vp-btn-title">简单版教程</span>
                  <span class="vp-btn-desc">阅读快速开始文档</span>
                </span>
              </button>
              <button class="vp-btn vp-btn-outline" @click="goDetailed()">
                <span class="vp-btn-icon">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="2" width="18" height="20" rx="2"/><rect x="6" y="5" width="12" height="8" rx="1" fill="currentColor" fill-opacity="0.12"/><line x1="6" y1="17" x2="18" y2="17"/><line x1="6" y1="20" x2="12" y2="20"/></svg>
                </span>
                <span class="vp-btn-text">
                  <span class="vp-btn-title">详细版教程</span>
                  <span class="vp-btn-desc">查看图文教程</span>
                </span>
              </button>
            </div>
            <button class="vp-back" @click="step = 'choice'">← 返回上一步</button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.vp-overlay {
  position: fixed;
  inset: 0;
  z-index: 1001;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.vp-dialog {
  position: relative;
  width: 480px;
  max-width: calc(100vw - 32px);
  border-radius: 16px;
  background: var(--vp-c-bg);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.25);
  overflow: hidden;
}

.vp-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--vp-c-text-2);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  z-index: 1;
}

.vp-close:hover {
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
}

.vp-body {
  padding: 32px 28px 28px;
  text-align: center;
}

.vp-title {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
  color: var(--vp-c-text-1);
}

.vp-subtitle {
  margin: 0 0 24px;
  font-size: 15px;
  color: var(--vp-c-text-2);
  line-height: 1.6;
}

.vp-actions {
  display: flex;
  gap: 12px;
}

.vp-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px 16px;
  border-radius: 12px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.vp-btn-primary {
  background: #ad96f4;
  color: #fff;
  border-color: #ad96f4;
}

.vp-btn-primary:hover {
  background: var(--vp-c-brand-2);
  border-color: var(--vp-c-brand-2);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(155, 132, 237, 0.3);
}

.vp-btn-outline {
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-divider);
}

.vp-btn-outline:hover {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-brand-soft);
  transform: translateY(-1px);
}

.vp-btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
}

.vp-btn-outline .vp-btn-icon {
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
}

.vp-btn-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.vp-btn-title {
  font-size: 15px;
  font-weight: 600;
}

.vp-btn-desc {
  font-size: 12px;
  opacity: 0.75;
}

.vp-back {
  margin-top: 16px;
  padding: 6px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--vp-c-text-2);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s;
}

.vp-back:hover {
  color: var(--vp-c-brand-1);
}
</style>
