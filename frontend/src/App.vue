<template>
  <main style="font-family: system-ui; padding: 24px; max-width: 720px; margin: 0 auto;">
    <h1>Air Alert Risk</h1>

    <div style="margin-top: 16px;">
      <label>Область</label>
      <div style="margin-top: 6px;">
        <select v-model="region" style="padding: 8px; width: 100%; max-width: 360px;">
          <option v-for="r in regions" :key="r.id" :value="r.id">
            {{ r.name }}
          </option>
        </select>
      </div>
    </div>

    <div style="margin-top: 16px; display:flex; gap: 8px; align-items:center;">
      <button @click="loadStatus" :disabled="loading" style="padding: 10px 14px;">
        {{ loading ? 'Loading...' : 'Оновити статус' }}
      </button>
      <span v-if="updatedAt" style="opacity: 0.7;">Оновлено: {{ updatedAt }}</span>
    </div>

    <div v-if="status" style="margin-top: 16px; padding: 12px; border-radius: 10px; background: #f6f6f6;">
      <div style="font-size: 18px;">
        Статус: <b>{{ statusText }}</b>
      </div>
      <pre style="margin-top: 10px;">{{ status }}</pre>
    </div>

    <p v-if="error" style="margin-top: 16px; color: #b00020;">{{ error }}</p>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

type Region = { id: string; name: string }

const regions = ref<Region[]>([])
const region = ref<string>('')

const loading = ref(false)
const error = ref<string | null>(null)
const status = ref<any | null>(null)
const updatedAt = ref<string | null>(null)

const statusText = computed(() => {
  if (!status.value) return ''
  if (status.value?.active === true) return 'Є тривога'
  if (status.value?.active === false) return 'Немає тривоги'
  return 'Невідомо'
})

async function loadRegions() {
  const res = await fetch('/api/regions')
  if (!res.ok) throw new Error(`regions: ${res.status}`)
  const json = await res.json()

  regions.value = json
  if (!region.value && regions.value.length) region.value = regions.value[0].id
}

async function loadStatus() {
  if (!region.value) return
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/status?region=${encodeURIComponent(region.value)}`)
    if (!res.ok) throw new Error(`status: ${res.status}`)
    status.value = await res.json()
    updatedAt.value = new Date().toLocaleString()
  } catch (e: any) {
    error.value = e?.message ?? 'Unknown error'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await loadRegions()
    await loadStatus()
  } catch (e: any) {
    error.value = e?.message ?? 'Failed to init'
  }
})
</script>
