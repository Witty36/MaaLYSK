import { detectEnvironment, isMirrorProjectLink } from './utils/mirror'

export async function enhanceMirrorLinks(version: string) {
  if (typeof document === 'undefined') return

  console.log('[mirror-enhance] version:', version)

  const isBeta = version.toLowerCase().includes('-beta')
    || version.toLowerCase().includes('-alpha')
    || version.toLowerCase().includes('-rc')
    || version.toLowerCase().includes('-pre')
  const channel = isBeta ? 'beta' : 'stable'

  const { platform, arch } = await detectEnvironment()

  const osMap: Record<string, string> = { windows: 'windows', macos: 'macos', linux: 'linux' }
  const archMap: Record<string, string> = { x64: 'x64', arm64: 'arm64' }
  const os = osMap[platform]
  const detectedArch = archMap[arch]

  console.log('[mirror-enhance] channel:', channel, 'os:', os, 'arch:', detectedArch)

  const allLinks = document.querySelectorAll<HTMLAnchorElement>('a[href]')
  let matched = 0
  allLinks.forEach(link => {
    if (!isMirrorProjectLink(link.href)) return
    matched++
    const url = new URL(link.href)
    url.searchParams.set('channel', channel)
    if (os) url.searchParams.set('os', os)
    if (detectedArch) url.searchParams.set('arch', detectedArch)
    link.href = url.toString()
  })
  console.log('[mirror-enhance] matched links:', matched)
}
