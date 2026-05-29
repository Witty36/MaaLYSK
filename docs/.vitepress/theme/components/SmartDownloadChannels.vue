<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useData } from 'vitepress'
import { detectEnvironment as detectEnv, type Platform, type Arch } from '../utils/mirror'

const props = withDefaults(defineProps<{
  detailHint?: string
}>(), {
  detailHint: '',
})

interface DownloadChannel {
  label: string
  href: string
  note?: string
}

interface DownloadRecommendation {
  button: string
  hint: string
  filename?: string
  tone: 'brand' | 'warning' | 'danger' | 'neutral'
}

const releaseFiles = {
  windows: {
    x64: 'MaaLYSK-win-x86_64-vx.x.x.zip',
    arm64: 'MaaLYSK-win-aarch64-vx.x.x.zip',
  },
  macos: {
    x64: 'MaaLYSK-macos-x86_64-vx.x.x.tar.gz',
    arm64: 'MaaLYSK-macos-aarch64-vx.x.x.tar.gz',
  },
  linux: {
    x64: 'MaaLYSK-linux-x86_64-vx.x.x.zip',
    arm64: 'MaaLYSK-linux-aarch64-vx.x.x.zip',
  },
} as const

function resolveFilename(template: string) {
  return template.replace('vx.x.x', latestVersion.value || 'vx.x.x')
}

const downloadChannels = computed<DownloadChannel[]>(() => {
  const isBeta = latestVersion.value.toLowerCase().includes('-beta')
    || latestVersion.value.toLowerCase().includes('-alpha')
    || latestVersion.value.toLowerCase().includes('-rc')
    || latestVersion.value.toLowerCase().includes('-pre')

  const params = new URLSearchParams({
    rid: 'MaaLYSK',
    channel: isBeta ? 'beta' : 'stable',
    source: 'maalysk-docs-download',
  })

  const osMap: Record<string, string> = {
    windows: 'windows',
    macos: 'macos',
    linux: 'linux',
  }
  const archMap: Record<string, string> = {
    x64: 'x64',
    arm64: 'arm64',
  }

  const os = osMap[detectedPlatform.value]
  const arch = archMap[detectedArch.value]

  if (os && arch) {
    params.set('os', os)
    params.set('arch', arch)
  }

  return [
    {
      label: 'Mirror酱',
      href: `https://mirrorchyan.com/zh/projects?${params.toString()}`,
      note: '高速下载，需购买 CDK',
    },
    {
      label: '百度网盘',
      href: 'https://pan.baidu.com/s/1qNgkEK1u2VRkGliY5jQfXQ?pwd=lysk',
      note: '更新可能不及时',
    },
    {
      label: 'GitHub',
      href: 'https://github.com/Witty36/MaaLYSK',
      note: '需科学上网',
    },
  ]
})

const rootRef = ref<HTMLElement | null>(null)
const detailsRef = ref<HTMLDetailsElement | null>(null)
const summaryRef = ref<HTMLElement | null>(null)
const { theme } = useData()

const latestVersion = computed(() => {
  const meta: any = theme.value.latestReleaseMeta
  return meta?.version ?? ''
})

const releaseDate = computed(() => {
  const meta: any = theme.value.latestReleaseMeta
  const raw = meta?.published_at
  if (!raw) return ''
  return raw.slice(0, 10)
})

const versionTypeLabel = computed(() => {
  const v = latestVersion.value.toLowerCase()
  if (v.includes('-beta') || v.includes('-alpha') || v.includes('-rc') || v.includes('-pre')) {
    return '公测版'
  }
  return '正式版'
})

const isClientReady = ref(false)
const isExpanded = ref(false)
const detectedPlatform = ref<Platform>('unknown')
const detectedArch = ref<Arch>('unknown')

async function detectEnvironment() {
  const env = await detectEnv()
  detectedPlatform.value = env.platform
  detectedArch.value = env.arch
}

function getArchDisplayName(arch: Arch): string {
  if (arch === 'x64') return 'x86_64'
  if (arch === 'arm64') return 'aarch64'
  return arch
}

const recommendation = computed<DownloadRecommendation>(() => {
  if (!isClientReady.value) {
    return {
      button: '查看全部下载渠道',
      hint: '正在识别当前系统与架构；若未自动推荐，可直接展开下方下载渠道手动选择安装包。',
      tone: 'neutral',
    }
  }

  const platform = detectedPlatform.value
  const arch = detectedArch.value

  // Windows
  if (platform === 'windows') {
    if (arch === 'x64' || arch === 'arm64') {
      const files = releaseFiles.windows
      return {
        button: `推荐下载 Windows ${getArchDisplayName(arch)} 版`,
        hint: '进入任一渠道后，优先选择以下完整安装包：',
        filename: resolveFilename(files[arch]),
        tone: 'brand',
      }
    }
    return {
      button: '推荐下载 Windows x86_64 版',
      hint: '未能识别 CPU 架构，推荐优先尝试 x86_64 版本；若无法运行，请选择 aarch64 版本。',
      filename: resolveFilename(releaseFiles.windows.x64),
      tone: 'warning',
    }
  }

  // macOS — both x64 (Intel) and arm64 (Apple Silicon) are supported
  if (platform === 'macos') {
    if (arch === 'x64') {
      return {
        button: '推荐下载 macOS Intel 版',
        hint: '进入任一渠道后，优先选择以下完整安装包：',
        filename: resolveFilename(releaseFiles.macos.x64),
        tone: 'brand',
      }
    }
    if (arch === 'arm64') {
      return {
        button: '推荐下载 macOS Apple Silicon 版',
        hint: '进入任一渠道后，优先选择以下完整安装包：',
        filename: resolveFilename(releaseFiles.macos.arm64),
        tone: 'brand',
      }
    }
    return {
      button: '推荐下载 macOS Apple Silicon 版',
      hint: '未能识别 CPU 架构，M 芯片用户请选择 aarch64 版本，Intel 用户请选择 x86_64 版本。',
      filename: resolveFilename(releaseFiles.macos.arm64),
      tone: 'warning',
    }
  }

  // Linux
  if (platform === 'linux') {
    if (arch === 'x64' || arch === 'arm64') {
      const files = releaseFiles.linux
      return {
        button: `推荐下载 Linux ${getArchDisplayName(arch)} 版`,
        hint: '进入任一渠道后，优先选择以下完整安装包（暂未完整测试）：',
        filename: resolveFilename(files[arch]),
        tone: 'brand',
      }
    }
    return {
      button: '推荐下载 Linux x86_64 版',
      hint: '未能识别 CPU 架构，推荐优先尝试 x86_64 版本（暂未完整测试）。',
      filename: resolveFilename(releaseFiles.linux.x64),
      tone: 'warning',
    }
  }

  if (platform === 'android') {
    return {
      button: 'Android 暂不支持',
      hint: 'MaaLYSK 当前不提供 Android 版本，请使用 Windows、macOS 或 Linux 设备运行。',
      tone: 'danger',
    }
  }

  if (platform === 'ios') {
    return {
      button: 'iOS 暂不支持',
      hint: 'MaaLYSK 当前不提供 iOS 版本，请使用 Windows、macOS 或 Linux 设备运行。',
      tone: 'danger',
    }
  }

  return {
    button: '当前系统暂不支持',
    hint: 'MaaLYSK 当前支持 Windows、macOS 与 Linux（x86_64 / aarch64）。',
    tone: 'danger',
  }
})

function getStickyOffset() {
  if (typeof document === 'undefined')
    return 0

  return ['.VPNav', '.VPSectionTabs', '.VPLocalNav']
    .map(selector => document.querySelector<HTMLElement>(selector)?.getBoundingClientRect().height ?? 0)
    .reduce((sum, height) => sum + height, 0)
}

function getPreferredScrollTarget() {
  let current = rootRef.value?.previousElementSibling ?? null

  while (current) {
    if (/^H[1-6]$/.test(current.tagName))
      return current as HTMLElement

    current = current.previousElementSibling
  }

  return summaryRef.value || detailsRef.value
}

function getNextDetailsBelow(): HTMLElement | null {
  let current: Element | null = rootRef.value

  while (current) {
    current = current.nextElementSibling
    if (current instanceof HTMLDetailsElement)
      return current
  }

  return null
}


async function revealChannels() {
  if (props.detailHint) {
    await nextTick()
    requestAnimationFrame(() => {
      const target = getNextDetailsBelow()
      if (!target)
        return

      const heroHeight = rootRef.value?.getBoundingClientRect().height ?? 0
      const extraGap = 12
      const top = window.scrollY + target.getBoundingClientRect().top - getStickyOffset() - heroHeight - extraGap

      window.scrollTo({
        top: Math.max(0, top),
        behavior: 'smooth',
      })
    })
    return
  }

  if (detailsRef.value && !detailsRef.value.open)
    detailsRef.value.open = true

  isExpanded.value = true

  await nextTick()

  requestAnimationFrame(() => {
    const target = getPreferredScrollTarget()
    if (!target)
      return

    const extraGap = 12
    const top = window.scrollY + target.getBoundingClientRect().top - getStickyOffset() - extraGap

    window.scrollTo({
      top: Math.max(0, top),
      behavior: 'smooth',
    })
  })
}

function syncExpandedState() {
  isExpanded.value = detailsRef.value?.open ?? false
}

onMounted(() => {
  void (async () => {
    await detectEnvironment()
    isClientReady.value = true
    syncExpandedState()
  })()
})
</script>

<template>
  <section ref="rootRef" class="smart-download" aria-label="智能下载渠道推荐">
    <div class="smart-download__hero">
      <div class="smart-download__action">
        <button
          type="button"
          class="smart-download__primary"
          :class="`smart-download__primary--${recommendation.tone}`"
          :aria-expanded="isExpanded ? 'true' : 'false'"
          aria-controls="download-channel-links"
          @click="revealChannels"
        >
          {{ recommendation.button }}
        </button>
        <span class="smart-download__action-tag">{{ props.detailHint ? '点击跳转至下方详情 ↓' : '点击展开下载渠道 ↓' }}</span>
      </div>
      <p class="smart-download__hint">
        {{ recommendation.hint }}
      </p>
      <p v-if="recommendation.filename" class="smart-download__filename">
        <code>{{ recommendation.filename }}</code>
        <span class="smart-download__version-label" :class="versionTypeLabel === '公测版' ? 'is-beta' : 'is-stable'">{{ versionTypeLabel }}</span>
      </p>
      <p v-if="recommendation.filename && releaseDate" class="smart-download__release-date">最新发布于 {{ releaseDate }}</p>
      <p v-else-if="latestVersion" class="smart-download__version">
        最新版本
        <span class="smart-download__version-tag">{{ latestVersion }}</span>
        <span class="smart-download__version-label" :class="versionTypeLabel === '公测版' ? 'is-beta' : 'is-stable'">{{ versionTypeLabel }}</span>
        <span v-if="releaseDate" class="smart-download__release-date--inline">{{ releaseDate }}</span>
      </p>
    </div>

    <details v-if="!props.detailHint" ref="detailsRef" class="smart-download__details" @toggle="syncExpandedState">
      <summary ref="summaryRef" class="smart-download__summary">
        查看全部下载渠道
      </summary>

      <div id="download-channel-links" class="smart-download__grid">
        <a
          v-for="channel in downloadChannels"
          :key="channel.label"
          class="smart-download__link"
          :href="channel.href"
          target="_blank"
          rel="noopener"
        >
          <span class="smart-download__link-main">{{ channel.label }}</span>
          <span v-if="channel.note" class="smart-download__link-note">{{ channel.note }}</span>
        </a>
      </div>
    </details>
  </section>
</template>

<style scoped>
.smart-download {
  margin: 18px 0 12px;
}

.smart-download__hero {
  display: grid;
  gap: 12px;
  padding: 18px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgb(99 102 241 / 12%), transparent 36%),
    linear-gradient(135deg, var(--vp-c-bg-soft), var(--vp-c-bg-elv));
  box-shadow: 0 16px 40px rgb(79 70 229 / 10%);
}

.dark .smart-download__hero {
  box-shadow: 0 18px 44px rgb(15 23 42 / 28%);
}

.smart-download__action {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.smart-download__action-tag {
  color: var(--vp-c-text-3);
  font-size: 0.85rem;
}

.smart-download__primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  min-height: 52px;
  padding: 0 18px;
  border: 0;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--vp-c-brand-3), var(--vp-c-brand-2));
  color: var(--vp-c-white);
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 14px 28px rgb(79 70 229 / 20%);
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

.smart-download__primary--warning {
  background: linear-gradient(135deg, var(--vp-c-warning-3), var(--vp-c-warning-2));
  color: var(--vp-c-black);
  box-shadow: 0 14px 28px rgb(234 179 8 / 18%);
}

.smart-download__primary--danger {
  background: linear-gradient(135deg, var(--vp-c-danger-3), var(--vp-c-danger-2));
  color: var(--vp-c-white);
  box-shadow: 0 14px 28px rgb(220 38 38 / 22%);
}

.smart-download__primary--neutral {
  background: linear-gradient(135deg, var(--vp-c-default-3), var(--vp-c-default-2));
  color: var(--vp-c-white);
  box-shadow: 0 14px 28px rgb(100 116 139 / 18%);
}

.smart-download__primary:hover {
  transform: translateY(-2px);
  filter: saturate(1.08);
  box-shadow: 0 18px 34px rgb(79 70 229 / 26%);
}

.smart-download__primary:active {
  transform: translateY(0);
}

.smart-download__hint {
  margin: 0;
  color: var(--vp-c-text-2);
  line-height: 1.7;
}

.smart-download__filename {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: -2px 0 0;
}

.smart-download__filename code {
  display: inline-block;
  max-width: 100%;
  padding: 8px 12px;
  border-radius: 10px;
  border: 1px solid color-mix(in srgb, var(--vp-c-brand-soft) 40%, transparent);
  background: color-mix(in srgb, var(--vp-c-brand-soft) 55%, transparent);
  color: var(--vp-c-text-2);
  font-size: 0.95rem;
  line-height: 1.5;
  white-space: normal;
  word-break: break-all;
}

.smart-download__release-date {
  margin: -2px 0 0;
  font-size: 0.78rem;
  color: rgba(150, 148, 165, 0.75);
}

.smart-download__release-date--inline {
  font-size: 0.68rem;
  color: rgba(148, 142, 175, 0.35);
}

.smart-download__version {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
  margin: -2px 0 0;
  color: rgba(140, 138, 160, 0.95);
  font-size: 0.78rem;
}

.smart-download__version-tag {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--vp-c-text-2);
  background: rgba(155, 132, 237, 0.04);
}

.smart-download__version-label {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 500;
}

.smart-download__version-label.is-stable {
  color: rgba(16, 185, 129, 0.88);
  background: rgba(16, 185, 129, 0.06);
}

.smart-download__version-label.is-beta {
  color: rgba(245, 158, 11, 0.88);
  background: rgba(245, 158, 11, 0.06);
}

.smart-download__version-date {
  color: rgba(155, 148, 185, 0.45);
  font-size: 0.65rem;
}

.smart-download__details {
  margin-top: 14px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 18px;
  background: color-mix(in srgb, var(--vp-c-bg-soft) 78%, transparent);
  overflow: hidden;
}

.smart-download__summary {
  list-style: none;
  padding: 14px 18px;
  cursor: pointer;
  user-select: none;
  font-weight: 700;
  color: var(--vp-c-text-1);
}

.smart-download__summary::-webkit-details-marker {
  display: none;
}

.smart-download__summary::after {
  content: '▾';
  float: right;
  color: var(--vp-c-brand-1);
  transition: transform 0.2s ease;
}

.smart-download__details[open] .smart-download__summary::after {
  transform: rotate(180deg);
}

.smart-download__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px;
  padding: 0 18px 18px;
}

.smart-download__link {
  display: grid;
  gap: 4px;
  min-height: 64px;
  padding: 14px 16px;
  border: 1px solid var(--vp-c-brand-soft);
  border-radius: 16px;
  background: linear-gradient(135deg, var(--vp-c-brand-soft), var(--vp-c-bg-soft));
  color: var(--vp-c-text-1);
  text-decoration: none;
  box-shadow: 0 10px 24px rgb(79 70 229 / 10%);
  transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease,
    background 0.2s ease;
}

.smart-download__link:hover {
  transform: translateY(-2px);
  border-color: var(--vp-c-brand-1);
  box-shadow: 0 16px 32px rgb(79 70 229 / 18%);
  background: linear-gradient(135deg, var(--vp-c-brand-soft), var(--vp-c-bg-elv));
}

.smart-download__link-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-weight: 700;
}

.smart-download__link-main::after {
  content: '↗';
  color: var(--vp-c-brand-1);
  font-size: 0.95rem;
}

.smart-download__link-note {
  color: var(--vp-c-text-2);
  font-size: 0.88rem;
}

@media (max-width: 640px) {
  .smart-download__hero {
    padding: 16px;
  }

  .smart-download__primary {
    width: 100%;
  }

  .smart-download__grid {
    grid-template-columns: 1fr;
    padding: 0 16px 16px;
  }
}
</style>
