<template>
  <div class="emoji-table-app">
    <!-- ============ PASSWORD GATE ============ -->
    <div v-if="!unlocked" class="password-gate">
      <div class="password-card">
        <div class="password-icon">
          <i class="ri-lock-line"></i>
        </div>
        <h2>Emoji 中文对照表</h2>
        <p class="password-desc">该页面仅对开发组成员开放，请输入密码查看</p>
        <div class="password-input-wrap">
          <div class="password-field">
            <input
              ref="passwordInputEl"
              v-model="passwordInput"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              class="password-input"
              @keyup.enter="tryUnlock"
            />
            <button type="button" class="password-eye" @click="showPassword = !showPassword" tabindex="-1">
              <i :class="showPassword ? 'ri-eye-off-line' : 'ri-eye-line'"></i>
            </button>
          </div>
          <button class="unlock-btn" @click="tryUnlock">解锁</button>
        </div>
        <p v-if="errorMsg" class="password-error">{{ errorMsg }}</p>
      </div>
    </div>

    <!-- ============ MAIN TABLE ============ -->
    <div v-else class="emoji-table-content">
      <!-- Top bar -->
      <div class="top-bar">
        <div class="top-bar-left">
          <span class="top-bar-title">Emoji 使用追踪</span>
          <span
            class="stats-badge"
            :class="{ 'filter-active': showUsedOnly }"
            @click="usedCount > 0 && (showUsedOnly = !showUsedOnly)"
            title="点击筛选已用"
          >
            {{ showUsedOnly ? '✓ 仅显示已用' : '已用' }}
            <strong>{{ usedCount }}</strong> / {{ totalCount }}
          </span>
          <span class="usage-percent">{{ usagePercent }}%</span>
        </div>
        <div class="top-bar-center">
          <div class="search-wrap">
            <i class="ri-search-line search-icon"></i>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索 Emoji 或中文名..."
              class="search-input"
            />
            <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">
              <i class="ri-close-line"></i>
            </button>
          </div>
        </div>
        <div class="top-bar-right">
          <button class="save-btn" :disabled="saving" @click="saveState">
            <i class="ri-save-line"></i>
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button class="clear-btn" @click="clearLocal" title="清除本地缓存">
            <i class="ri-delete-back-line"></i> 清除缓存
          </button>
        </div>
        <div class="top-bar-nav">
          <button class="sidebar-toggle-btn" @click="sidebarOpen = !sidebarOpen" title="分类导航">
            <i :class="sidebarOpen ? 'ri-close-line' : 'ri-menu-line'"></i> 导航
          </button>
        </div>
        <!-- Progress bar -->
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: usagePercent + '%' }"></div>
        </div>
      </div>

      <!-- Save status toast -->
      <div v-if="saveStatus" class="save-toast" :class="saveStatusType">
        <i :class="saveStatusType === 'success' ? 'ri-check-line' : 'ri-information-line'"></i>
        {{ saveStatus }}
        <button class="toast-close" @click="saveStatus = ''">&times;</button>
      </div>

      <!-- Copy toast -->
      <div v-if="copiedEmoji" class="copy-toast">
        已复制 {{ copiedEmoji }}
      </div>

      <!-- Save confirm modal -->
      <div v-if="pendingSave" class="token-overlay" @click.self="cancelSave">
        <div class="token-modal save-confirm-modal">
          <h3><i class="ri-git-repository-line"></i> 确认保存</h3>
          <p class="confirm-desc">
            将 <strong>{{ usedCount }}</strong> 个已标记的 Emoji
            提交到 <strong>Witty36/MaaLYSK</strong> 仓库
          </p>
          <div class="confirm-actions">
            <button class="clear-btn" @click="cancelSave">取消</button>
            <button class="save-btn" @click="confirmSave">提交</button>
          </div>
        </div>
      </div>

      <!-- Clear confirm modal -->
      <div v-if="pendingClear" class="token-overlay" @click.self="cancelClear">
        <div class="token-modal save-confirm-modal">
          <h3><i class="ri-delete-back-line"></i> 清除本地缓存</h3>
          <p class="confirm-desc">
            将清空本次编辑的勾选状态，恢复到最近一次<strong>已保存</strong>的状态。
          </p>
          <div class="confirm-actions">
            <button class="clear-btn" @click="cancelClear">取消</button>
            <button class="save-btn" @click="confirmClear">确认清除</button>
          </div>
        </div>
      </div>

      <!-- Two-column layout -->
      <div class="table-layout">
        <!-- Left: Category sidebar -->
        <nav class="category-sidebar" :class="{ open: sidebarOpen }">
          <div class="sidebar-inner">
            <div
              v-for="section in emojiSections"
              :key="section.id"
              class="sidebar-section"
            >
              <a
                :href="'#' + section.id"
                class="sidebar-section-link"
                @click.prevent="goTo(section.id)"
              >
                {{ section.title }}
              </a>
              <a
                v-for="cat in section.categories"
                :key="cat.id"
                :href="'#' + cat.id"
                class="sidebar-cat-link"
                :class="{ active: activeCategory === cat.id }"
                @click.prevent="goTo(cat.id)"
              >
                <span>{{ cat.title }}</span>
                <span class="cat-count">{{ cat.items.length }}</span>
              </a>
            </div>
          </div>
        </nav>

        <!-- Right: Emoji grid area -->
        <main class="emoji-grid-area">
          <!-- Search results -->
          <template v-if="searchQuery">
            <h2 class="section-heading">搜索结果（{{ searchResults.length }}）</h2>
            <template v-for="(group, gIdx) in groupedSearchResults" :key="gIdx">
              <h3 class="category-heading search-cat-heading" @click="goToCategory(group.firstSi, group.firstCi)">
                {{ group.label }} <i class="ri-arrow-right-line"></i>
              </h3>
              <div class="emoji-grid">
                <div
                  v-for="(r, idx) in group.items"
                  :key="idx"
                  class="emoji-card"
                  :class="{ used: isUsed(r.si, r.ci, r.ei) }"
                  :title="r.item.n + ' — 点击标记使用'"
                  @click="markUsed(r.si, r.ci, r.ei)"
                >
                  <button class="copy-btn" @click.stop="copyEmoji(r.item)" title="复制">
                    <i class="ri-file-copy-line"></i>
                  </button>
                  <span class="emoji-char">{{ r.item.e }}</span>
                  <span class="emoji-name">{{ r.item.n }}</span>
                  <div class="checkbox-overlay">
                    <span v-if="isUsed(r.si, r.ci, r.ei)" class="used-tag">
                      <i class="ri-check-line"></i> 已用
                    </span>
                    <span v-else class="unused-tag">可用</span>
                  </div>
                </div>
              </div>
            </template>
          </template>

          <!-- Full category view (when not searching) -->
          <template v-else>
            <template v-for="(section, si) in emojiSections" :key="section.id">
              <template v-for="(cat, ci) in section.categories" :key="cat.id">
                <!-- Skip empty categories when filtering used-only -->
                <template v-if="!showUsedOnly || catHasUsed(si, ci)">
                  <h2 v-if="!showUsedOnly" :id="section.id" class="section-heading">{{ section.title }}</h2>
                  <h3 v-if="showUsedOnly" class="category-heading used-cat-heading" @click="goToCategory(si, ci)">
                    {{ section.title }} · {{ cat.title }} <i class="ri-arrow-right-line"></i>
                  </h3>
                  <h3 v-else :id="cat.id" class="category-heading">{{ cat.title }}</h3>
                  <div class="emoji-grid">
                    <div
                      v-for="(item, ei) in cat.items"
                      :key="ei"
                      v-show="!showUsedOnly || isUsed(si, ci, ei)"
                      class="emoji-card"
                      :class="{ used: isUsed(si, ci, ei) }"
                      :title="item.n + ' — 点击卡片标记使用'"
                      @click="markUsed(si, ci, ei)"
                    >
                      <button class="copy-btn" @click.stop="copyEmoji(item)" title="复制">
                        <i class="ri-file-copy-line"></i>
                      </button>
                      <span class="emoji-char">{{ item.e }}</span>
                      <span class="emoji-name">{{ item.n }}</span>
                      <div class="checkbox-overlay">
                        <span v-if="isUsed(si, ci, ei)" class="used-tag">
                          <i class="ri-check-line"></i> 已用
                        </span>
                        <span v-else class="unused-tag">可用</span>
                      </div>
                    </div>
                  </div>
                </template>
              </template>
            </template>
          </template>
        </main>
      </div>

      <!-- Mobile sidebar overlay -->
      <div class="sidebar-overlay" :class="{ show: sidebarOpen }" @click="sidebarOpen = false"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { emojiSections } from './emojiData'

// ===================== PASSWORD =====================
const UNLOCK_KEY = 'emoji_unlocked'
const unlocked = ref(false)
const passwordInput = ref('')
const showPassword = ref(false)
const errorMsg = ref('')
const passwordInputEl = ref<HTMLInputElement | null>(null)

// ⚠️ 开发组密码在这里修改：
const CORRECT_PASSWORD = 'MaaLYSK0306'

function tryUnlock() {
  if (passwordInput.value === CORRECT_PASSWORD) {
    unlocked.value = true
    localStorage.setItem(UNLOCK_KEY, '1')
    errorMsg.value = ''
    loadState()
    nextTick(() => {
      initScrollSpy()
    })
  } else {
    errorMsg.value = '密码错误，请重试'
    passwordInput.value = ''
    passwordInputEl.value?.focus()
  }
}

// ===================== SEARCH =====================
const searchQuery = ref('')
const copiedEmoji = ref('')
const sidebarOpen = ref(false)

const groupedSearchResults = computed(() => {
  const groups: Map<string, { label: string; firstSi: number; firstCi: number; items: any[] }> = new Map()
  for (const r of searchResults.value) {
    const section = emojiSections[r.si]
    const cat = section.categories[r.ci]
    const label = cat.title !== section.title ? section.title + ' · ' + cat.title : section.title
    if (!groups.has(label)) groups.set(label, { label, firstSi: r.si, firstCi: r.ci, items: [] })
    groups.get(label)!.items.push(r)
  }
  return [...groups.values()]
})

const searchResults = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return []
  const results: { si: number; ci: number; ei: number; item: any }[] = []
  for (let si = 0; si < emojiSections.length; si++) {
    for (let ci = 0; ci < emojiSections[si].categories.length; ci++) {
      for (let ei = 0; ei < emojiSections[si].categories[ci].items.length; ei++) {
        const item = emojiSections[si].categories[ci].items[ei]
        if (item.e.includes(q) || item.n.toLowerCase().includes(q)) {
          results.push({ si, ci, ei, item })
        }
      }
    }
  }
  return results
})

async function copyEmoji(item: { e: string; n: string }) {
  try {
    await navigator.clipboard.writeText(item.e)
    copiedEmoji.value = item.e + ' ' + item.n
    setTimeout(() => { copiedEmoji.value = '' }, 1500)
  } catch {
    // Fallback for older browsers
    const ta = document.createElement('textarea')
    ta.value = item.e
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copiedEmoji.value = item.e + ' ' + item.n
    setTimeout(() => { copiedEmoji.value = '' }, 1500)
  }
}

// ===================== USAGE STATE =====================
const LOCAL_KEY = 'emoji_used'
// flat index for each emoji: usedSet stores flat indices
const flatIndices: { si: number; ci: number; ei: number }[] = []
for (let si = 0; si < emojiSections.length; si++) {
  for (let ci = 0; ci < emojiSections[si].categories.length; ci++) {
    const items = emojiSections[si].categories[ci].items
    for (let ei = 0; ei < items.length; ei++) {
      flatIndices.push({ si, ci, ei })
    }
  }
}
const totalCount = flatIndices.length

const usedSet = ref<Set<string>>(new Set())

function key(si: number, ci: number, ei: number): string {
  return `${si}-${ci}-${ei}`
}

function isUsed(si: number, ci: number, ei: number): boolean {
  return usedSet.value.has(key(si, ci, ei))
}

function markUsed(si: number, ci: number, ei: number) {
  const k = key(si, ci, ei)
  if (usedSet.value.has(k)) {
    usedSet.value.delete(k)  // 取消勾选
  } else {
    usedSet.value.add(k)     // 标记已用
  }
  saveLocal()
}

function catHasUsed(si: number, ci: number): boolean {
  for (let ei = 0; ei < emojiSections[si].categories[ci].items.length; ei++) {
    if (isUsed(si, ci, ei)) return true
  }
  return false
}

function saveLocal() {
  localStorage.setItem(LOCAL_KEY, JSON.stringify([...usedSet.value]))
}

const usedCount = computed(() => usedSet.value.size)
const usagePercent = computed(() =>
  totalCount === 0 ? 0 : Math.round((usedCount.value / totalCount) * 100)
)

const usedItems = computed(() => {
  const list: { key: string; e: string; n: string }[] = []
  for (let si = 0; si < emojiSections.length; si++) {
    for (let ci = 0; ci < emojiSections[si].categories.length; ci++) {
      for (let ei = 0; ei < emojiSections[si].categories[ci].items.length; ei++) {
        if (isUsed(si, ci, ei)) {
          const item = emojiSections[si].categories[ci].items[ei]
          list.push({ key: key(si, ci, ei), e: item.e, n: item.n })
        }
      }
    }
  }
  return list
})

// ===================== GITHUB API SAVE =====================
const GITHUB_OWNER = 'Witty36'
const GITHUB_REPO = 'MaaLYSK'
const SAVE_FILE_PATH = 'docs/public/zh_cn/develop/2.2-emoji-usage.json'
const SAVE_BRANCH = 'main'

async function commitToGitHubAPI(token: string, content: string): Promise<{ newFile: boolean }> {
  const apiBase = 'https://api.github.com'
  const apiPath = `/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/${encodeURIComponent(SAVE_FILE_PATH)}`

  // 1. Get current file SHA (if exists)
  let sha: string | null = null
  try {
    const getResp = await fetch(apiBase + apiPath, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
      },
    })
    if (getResp.ok) {
      const data = await getResp.json()
      if (data.sha) sha = data.sha
    }
  } catch {
    // File doesn't exist yet
  }

  // 2. Create or update
  const payload: any = {
    message: 'chore: update emoji usage state\n\n[auto] via EmojiTable save',
    content: btoa(unescape(encodeURIComponent(content))),
    branch: SAVE_BRANCH,
  }
  if (sha) payload.sha = sha

  const putResp = await fetch(apiBase + apiPath, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!putResp.ok) {
    const err = await putResp.json().catch(() => ({ message: `HTTP ${putResp.status}` }))
    throw new Error(err.message || `GitHub API error ${putResp.status}`)
  }

  return { newFile: !sha }
}
const pendingSave = ref(false)
const saving = ref(false)
const saveStatus = ref('')
const saveStatusType = ref<'success' | 'info'>('info')

function showSaveConfirm() {
  pendingSave.value = true
}

function confirmSave() {
  pendingSave.value = false
  doSave()
}

function cancelSave() {
  pendingSave.value = false
}

async function saveState() {
  showSaveConfirm()
}

async function doSave() {
  saving.value = true
  saveStatus.value = ''

  const payload = {
    version: 1,
    used: [...usedSet.value],
    lastSaved: new Date().toISOString(),
  }
  const jsonStr = JSON.stringify(payload, null, 2)

  // Strategy A: Dev server endpoint — 本地开发时直接写文件
  try {
    const resp = await fetch('/__emoji-save__', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonStr,
    })
    if (resp.ok) {
      const result = await resp.json()
      if (result.method === 'github') {
        saveStatus.value = '✅ ' + result.message
        saveStatusType.value = 'success'
      } else {
        saveStatus.value = '💾 已保存到本地文件'
        saveStatusType.value = 'success'
      }
      saving.value = false
      setTimeout(() => { saveStatus.value = '' }, 4000)
      return
    }
  } catch { /* dev server not running, fall through */ }

  // Strategy B: GitHub API — 线上部署时用内置 token 直接提交
  const token = (import.meta.env.VITE_EMOJI_TOKEN as string) || ''
  if (token && token.length > 0) {
    try {
      await commitToGitHubAPI(token, jsonStr)
      saveStatus.value = '✅ 已保存到 GitHub 仓库！全组即时同步。'
      saveStatusType.value = 'success'
      saving.value = false
      setTimeout(() => { saveStatus.value = '' }, 5000)
      return
    } catch (err: any) {
      saveStatus.value = '❌ GitHub 提交失败: ' + (err.message || err)
      saveStatusType.value = 'info'
      saving.value = false
      setTimeout(() => { saveStatus.value = '' }, 8000)
      return
    }
  }

  // Strategy C: Download as file — 最后的兜底
  const blob = new Blob([jsonStr], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = '2.2-emoji-usage.json'
  a.click()
  URL.revokeObjectURL(url)
  saveStatus.value = '📥 已下载 JSON，请手动替换并提交。'
  saveStatusType.value = 'info'
  saving.value = false
  setTimeout(() => { saveStatus.value = '' }, 6000)
}

// ===================== CLEAR LOCAL =====================
const pendingClear = ref(false)
const showUsedOnly = ref(false)

function showClearConfirm() {
  pendingClear.value = true
}

function confirmClear() {
  pendingClear.value = false
  usedSet.value = new Set()
  localStorage.removeItem(LOCAL_KEY)
  loadFromJSON()
}

function cancelClear() {
  pendingClear.value = false
}

function clearLocal() {
  showClearConfirm()
}

// ===================== CATEGORY SCROLL SPY =====================
const activeCategory = ref('')
let observer: IntersectionObserver | null = null

function initScrollSpy() {
  // Clean up old observer
  if (observer) observer.disconnect()

  const headings = document.querySelectorAll('.category-heading')
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activeCategory.value = entry.target.id
        }
      }
    },
    { rootMargin: '-150px 0px -60% 0px' }
  )
  headings.forEach((h) => observer!.observe(h))
}

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})

function goTo(id: string) {
  sidebarOpen.value = false
  searchQuery.value = ''
  nextTick(() => scrollToSection(id))
}

function goToCategory(si: number, ci: number) {
  const cat = emojiSections[si].categories[ci]
  searchQuery.value = ''
  showUsedOnly.value = false
  sidebarOpen.value = false
  nextTick(() => scrollToSection(cat.id))
}

function scrollToSection(id: string) {
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeCategory.value = id
    // Adjust for fixed header
    setTimeout(() => {
      const top = el.getBoundingClientRect().top + window.scrollY - 150
      window.scrollTo({ top, behavior: 'smooth' })
    }, 50)
  }
}

// ===================== LIFECYCLE =====================
function loadFromJSON() {
  const jsonPath = '/zh_cn/develop/2.2-emoji-usage.json?_t=' + Date.now()
  fetch(jsonPath)
    .then((r) => r.json())
    .then((data) => {
      if (data.used && Array.isArray(data.used)) {
        usedSet.value = new Set(data.used)
        localStorage.setItem(LOCAL_KEY, JSON.stringify(data.used))
      }
    })
    .catch(() => {
      // File doesn't exist yet, keep current state
    })
}

function loadState() {
  // 1. Load from localStorage (fast, offline-capable)
  const local = localStorage.getItem(LOCAL_KEY)
  if (local) {
    try {
      usedSet.value = new Set(JSON.parse(local))
    } catch { /* ignore */ }
  }
  // 2. Then override with server JSON (authoritative)
  loadFromJSON()
}

onMounted(() => {
  // Check if previously unlocked
  if (localStorage.getItem(UNLOCK_KEY) === '1') {
    unlocked.value = true
    loadState()
    nextTick(() => {
      initScrollSpy()
    })
  } else {
    nextTick(() => {
      passwordInputEl.value?.focus()
    })
  }

  // Listen for Vite's HMR full-reload to re-init scroll spy
  if (import.meta.hot) {
    import.meta.hot.on('vite:afterUpdate', () => {
      if (unlocked.value) {
        nextTick(() => initScrollSpy())
      }
    })
  }
})
</script>

<style scoped>
/* ==================== PASSWORD GATE ==================== */
.password-gate {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px 20px;
}

.password-card {
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 48px 40px;
  text-align: center;
  max-width: 420px;
  width: 100%;
}

.password-icon {
  font-size: 48px;
  color: var(--vp-c-brand-1);
  margin-bottom: 16px;
}

.password-card h2 {
  font-size: 22px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--vp-c-text-1);
}

.password-desc {
  font-size: 14px;
  color: var(--vp-c-text-2);
  margin: 0 0 24px;
}

.password-input-wrap {
  display: flex;
  gap: 8px;
}

.password-field {
  flex: 1;
  position: relative;
}

.password-input {
  width: 100%;
  padding: 10px 40px 10px 16px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  font-size: 16px;
  outline: none;
  transition: border-color 0.2s;
}

.password-input:focus {
  border-color: var(--vp-c-brand-1);
}

.password-eye {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--vp-c-text-3);
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.password-eye:hover {
  color: var(--vp-c-text-1);
}

.unlock-btn {
  padding: 10px 20px;
  background: var(--vp-c-brand-1);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
  white-space: nowrap;
}

.unlock-btn:hover {
  background: var(--vp-c-brand-2);
}

.password-error {
  color: #e74c3c;
  font-size: 14px;
  margin: 12px 0 0;
}

/* ==================== TOP BAR ==================== */
.top-bar {
  position: sticky;
  top: 64px; /* below VP nav */
  z-index: 10;
  background: var(--vp-c-bg);
  border-bottom: 1px solid var(--vp-c-divider);
  padding: 12px 16px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.top-bar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.top-bar-title {
  font-weight: 600;
  font-size: 15px;
  color: var(--vp-c-text-1);
}

.stats-badge {
  background: var(--vp-c-brand-1);
  color: #fff;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}

.stats-badge:hover {
  background: var(--vp-c-brand-2);
}

.stats-badge strong {
  font-weight: 700;
}

.usage-percent {
  font-size: 13px;
  color: var(--vp-c-text-2);
}

.top-bar-right {
  display: flex;
  gap: 8px;
}

.top-bar-nav {
  display: none;
}

.save-btn, .clear-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--vp-c-divider);
  transition: all 0.2s;
}

.save-btn {
  background: var(--vp-c-brand-1);
  color: #fff;
  border-color: var(--vp-c-brand-1);
}

.save-btn:hover:not(:disabled) {
  background: var(--vp-c-brand-2);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.clear-btn {
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-2);
}

.clear-btn:hover {
  color: var(--vp-c-text-1);
  border-color: var(--vp-c-text-3);
}

.progress-track {
  width: 100%;
  height: 3px;
  background: var(--vp-c-divider);
  border-radius: 2px;
  overflow: hidden;
  flex-basis: 100%;
}

.progress-fill {
  height: 100%;
  background: var(--vp-c-brand-1);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* ==================== SEARCH ==================== */
.search-wrap {
  position: relative;
  width: 100%;
  max-width: 320px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  color: var(--vp-c-text-3);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 6px 32px 6px 32px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  font-size: 13px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: var(--vp-c-brand-1);
}

.search-clear {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--vp-c-text-3);
  cursor: pointer;
  font-size: 14px;
  padding: 2px;
}

.search-clear:hover {
  color: var(--vp-c-text-1);
}

/* ==================== COPY TOAST ==================== */
.copy-toast {
  position: fixed;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  padding: 8px 18px;
  border-radius: 8px;
  background: #333;
  color: #fff;
  font-size: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  animation: copyFadeIn 0.2s ease;
}

@keyframes copyFadeIn {
  from { opacity: 0; transform: translateX(-50%) translateY(-8px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}

/* ==================== SAVE TOAST ==================== */
.save-toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  max-width: 600px;
}

.save-toast.success {
  background: #27ae60;
  color: #fff;
}

.save-toast.info {
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-1);
  border: 1px solid var(--vp-c-divider);
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  font-size: 18px;
  cursor: pointer;
  margin-left: 8px;
  opacity: 0.7;
}

.toast-close:hover {
  opacity: 1;
}

/* ==================== TWO-COLUMN LAYOUT ==================== */
.table-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 0;
  min-height: 60vh;
}

/* ==================== SIDEBAR ==================== */
.category-sidebar {
  background: var(--vp-c-bg-soft);
  border-right: 1px solid var(--vp-c-divider);
  overflow-y: auto;
  max-height: calc(100vh - 130px);
  position: sticky;
  top: 120px;
}

.sidebar-inner {
  padding: 16px 12px;
}

.sidebar-section {
  margin-bottom: 16px;
}

.sidebar-section-link {
  display: block;
  padding: 4px 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--vp-c-text-1);
  text-decoration: none;
  border-radius: 4px;
  margin-bottom: 2px;
}

.sidebar-section-link:hover {
  color: var(--vp-c-brand-1);
}

.sidebar-cat-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 8px 3px 16px;
  font-size: 12px;
  color: var(--vp-c-text-2);
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.15s;
}

.sidebar-cat-link:hover {
  color: var(--vp-c-text-1);
  background: var(--vp-c-bg-mute);
}

.sidebar-cat-link.active {
  color: var(--vp-c-brand-1);
  background: var(--vp-c-bg-mute);
  font-weight: 500;
}

.cat-count {
  font-size: 11px;
  color: var(--vp-c-text-3);
  background: var(--vp-c-bg);
  padding: 0 6px;
  border-radius: 8px;
}

/* ==================== EMOJI GRID ==================== */
.emoji-grid-area {
  padding: 16px 24px 40px;
}

.section-heading {
  font-size: 20px;
  font-weight: 600;
  margin: 32px 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--vp-c-brand-1);
  color: var(--vp-c-text-1);
  scroll-margin-top: 150px;
}

.section-heading:first-child {
  margin-top: 8px;
}

.search-cat-heading,
.used-cat-heading {
  cursor: pointer;
  transition: color 0.15s;
}

.search-cat-heading:hover,
.used-cat-heading:hover {
  color: var(--vp-c-brand-1);
}

.search-cat-heading i,
.used-cat-heading i {
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.15s;
}

.search-cat-heading:hover i,
.used-cat-heading:hover i {
  opacity: 0.7;
}

.category-heading {
  font-size: 15px;
  font-weight: 500;
  color: var(--vp-c-text-2);
  margin: 20px 0 10px;
  padding-left: 4px;
  scroll-margin-top: 150px;
  overflow-wrap: break-word;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}

/* ==================== EMOJI CARD ==================== */
.copy-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  color: var(--vp-c-text-3);
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s;
  z-index: 2;
}

/* 触屏设备：始终显示复制按钮，避免 :hover 误触 */
@media (hover: none) {
  .copy-btn {
    opacity: 0.4;
  }
}

.emoji-card:hover .copy-btn {
  opacity: 1;
}

.copy-btn:hover {
  background: var(--vp-c-brand-1);
  color: #fff;
  border-color: var(--vp-c-brand-1);
}

.emoji-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 6px;
  border-radius: 8px;
  border: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg-soft);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  user-select: none;
}

.emoji-card:hover {
  border-color: var(--vp-c-brand-1);
  background: var(--vp-c-bg-mute);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.emoji-card.used {
  opacity: 0.45;
  border-color: transparent;
  cursor: not-allowed;
  position: relative;
}

.emoji-card.used::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 4px,
    rgba(0, 0, 0, 0.03) 4px,
    rgba(0, 0, 0, 0.03) 8px
  );
  border-radius: 8px;
  pointer-events: none;
}

.emoji-card.used:hover {
  transform: none;
  box-shadow: none;
  border-color: var(--vp-c-divider);
}

.emoji-char {
  font-size: 28px;
  line-height: 1.4;
}

.emoji-name {
  font-size: 11px;
  color: var(--vp-c-text-2);
  margin-top: 4px;
  text-align: center;
  line-height: 1.2;
  word-break: keep-all;
}

.checkbox-overlay {
  margin-top: 6px;
  width: 100%;
  text-align: center;
}

.used-tag {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 10px;
  padding: 1px 8px;
  border-radius: 10px;
  background: var(--vp-c-brand-1);
  color: #fff;
  font-weight: 500;
}

.unused-tag {
  font-size: 10px;
  color: var(--vp-c-text-3);
  padding: 1px 8px;
}

/* ==================== SIDEBAR TOGGLE ==================== */
.sidebar-toggle-btn {
  display: none;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 6px;
  background: var(--vp-c-brand-1);
  color: #fff;
  border: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  line-height: 1;
}

.sidebar-toggle-btn:hover {
  background: var(--vp-c-brand-2);
}

/* ==================== MODAL OVERLAY ==================== */
.token-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.token-modal {
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  padding: 32px;
  max-width: 520px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.token-modal h3 {
  font-size: 18px;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--vp-c-text-1);
}

/* ==================== USED FILTER ==================== */
.stats-badge.filter-active {
  background: #27ae60;
  cursor: pointer;
}

.stats-badge.filter-active:hover {
  background: #219a52;
}

/* ==================== SAVE CONFIRM MODAL ==================== */
.save-confirm-modal {
  max-width: 380px;
  text-align: center;
}

.confirm-desc {
  font-size: 15px;
  color: var(--vp-c-text-2);
  margin: 0 0 24px;
  line-height: 1.6;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.confirm-actions .save-btn,
.confirm-actions .clear-btn {
  padding: 8px 24px;
  font-size: 14px;
}

/* ==================== RESPONSIVE ==================== */
@media (max-width: 768px) {
  .copy-btn {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }

  .sidebar-toggle-btn {
    display: inline-flex;
  }

  .table-layout {
    grid-template-columns: 1fr;
  }

  .category-sidebar {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 260px;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    max-height: 100vh;
    box-shadow: 2px 0 12px rgba(0, 0, 0, 0.15);
  }

  .category-sidebar.open {
    transform: translateX(0);
  }

  .sidebar-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 199;
  }

  .sidebar-overlay.show {
    display: block;
  }

  .emoji-grid {
    grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
    gap: 6px;
  }

  .emoji-card {
    padding: 8px 4px;
  }

  .emoji-char {
    font-size: 24px;
  }

  .top-bar {
    top: 48px;
    padding: 6px 8px;
    gap: 6px;
  }

  .top-bar-title {
    display: none;
  }

  .top-bar-left {
    gap: 6px;
    flex-shrink: 1;
  }

  .top-bar-center {
    flex: 1;
    order: 3;
    flex-basis: auto;
  }

  .top-bar-nav {
    order: 4;
    flex-shrink: 0;
  }

  .top-bar-nav {
    display: flex;
  }

  .top-bar-nav .sidebar-toggle-btn {
    display: inline-flex;
    padding: 0 12px;
    font-size: 13px;
    height: 36px;
  }

  .top-bar-right {
    gap: 4px;
    flex-shrink: 0;
  }

  .save-btn, .clear-btn {
    padding: 4px 10px;
    font-size: 12px;
  }

  .search-wrap {
    max-width: 100%;
  }

  .stats-badge {
    padding: 2px 8px;
    font-size: 12px;
    white-space: nowrap;
  }

  .password-input-wrap {
    flex-direction: column;
    align-items: stretch;
  }

  .password-field {
    width: 100%;
  }

  .unlock-btn {
    width: 100%;
  }

  .emoji-grid-area {
    padding: 12px 8px 32px;
  }

  .section-heading {
    font-size: 17px;
    margin: 20px 0 10px;
    scroll-margin-top: 120px;
  }

  .category-heading {
    font-size: 13px;
    margin: 12px 0 6px;
    scroll-margin-top: 120px;
  }

  .search-cat-heading,
  .used-cat-heading {
    padding-right: 4px;
  }
}
</style>
