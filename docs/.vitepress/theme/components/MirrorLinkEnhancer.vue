<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useData, useRouter } from 'vitepress'
import { enhanceMirrorLinks } from '../enhanceMirrorLinks'

const { theme } = useData()
const router = useRouter()

const runEnhance = () => {
  const version = theme.value.latestReleaseMeta?.version ?? ''
  if (version) enhanceMirrorLinks(version)
}

onMounted(() => {
  runEnhance()
  watch(() => router.route.path, () => setTimeout(runEnhance, 300))
})
</script>

<template />
