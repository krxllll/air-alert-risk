<template>
  <span class="badge" :class="cls">{{ text }}</span>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { pct, clamp01 } from "../utils/format";

const props = defineProps<{ risk: number }>();

const cls = computed(() => {
  const r = clamp01(props.risk);
  if (r >= 0.7) return "hi";
  if (r >= 0.4) return "mid";
  return "lo";
});

const text = computed(() => pct(props.risk));
</script>

<style scoped>
.badge { display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid #ddd; }
.lo { background: #f5f9ff; }
.mid { background: #fff7e6; }
.hi { background: #ffecec; }
</style>
