export type Platform = 'windows' | 'macos' | 'linux' | 'android' | 'ios' | 'unknown'
export type Arch = 'x64' | 'arm64' | 'arm' | 'unknown'

export function normalizePlatform(raw: string): Platform {
  const value = raw.toLowerCase()
  if (/(iphone|ipad|ipod|ios)/.test(value)) return 'ios'
  if (/android/.test(value)) return 'android'
  if (/(mac|darwin|os x)/.test(value)) return 'macos'
  if (/(win|windows)/.test(value)) return 'windows'
  if (/linux|x11/.test(value)) return 'linux'
  return 'unknown'
}

export function normalizeArch(raw: string): Arch {
  const value = raw.toLowerCase()
  if (/(arm64|aarch64|armv8|apple\s?silicon)/.test(value)) return 'arm64'
  if (/(arm|armv7)/.test(value)) return 'arm'
  if (/(x86_64|x64|win64|wow64|amd64|intel|x86)/.test(value)) return 'x64'
  return 'unknown'
}

export async function detectEnvironment(): Promise<{ platform: Platform; arch: Arch }> {
  if (typeof navigator === 'undefined') {
    return { platform: 'unknown', arch: 'unknown' }
  }

  const nav = navigator as Navigator & {
    userAgentData?: {
      platform?: string
      architecture?: string
      getHighEntropyValues?: (hints: string[]) => Promise<{ architecture?: string }>
    }
  }

  const userAgent = nav.userAgent ?? ''
  const platformHint = [nav.userAgentData?.platform, nav.platform, userAgent].filter(Boolean).join(' ')
  const platform = normalizePlatform(platformHint)

  if (platform === 'macos') {
    const macHints = [nav.userAgentData?.architecture].filter(Boolean) as string[]
    if (nav.userAgentData?.getHighEntropyValues) {
      try {
        const hints = await nav.userAgentData.getHighEntropyValues(['architecture'])
        if (hints.architecture) macHints.unshift(hints.architecture)
      } catch { /* ignore */ }
    }
    const detected = normalizeArch(macHints.join(' '))
    return { platform, arch: detected === 'unknown' ? 'arm64' : detected }
  }

  const archHint = [nav.userAgentData?.architecture, userAgent, nav.platform].filter(Boolean).join(' ')
  return { platform, arch: normalizeArch(archHint) }
}

export function buildMirrorProjectUrl(opts: {
  rid?: string
  channel?: string
  source?: string
  os?: string
  arch?: string
} = {}): string {
  const params = new URLSearchParams({
    rid: opts.rid ?? 'MaaLYSK',
    source: opts.source ?? 'maalysk-docs',
  })
  if (opts.channel) params.set('channel', opts.channel)
  if (opts.os) params.set('os', opts.os)
  if (opts.arch) params.set('arch', opts.arch)
  return `https://mirrorchyan.com/zh/projects?${params.toString()}`
}

export function isMirrorProjectLink(url: string): boolean {
  if (!/^https?:\/\/mirrorchyan\.com\/zh\/projects(\?|$)/.test(url)) return false
  try {
    return new URL(url).searchParams.get('rid') === 'MaaLYSK'
  } catch {
    return false
  }
}
