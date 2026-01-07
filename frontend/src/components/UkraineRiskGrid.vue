<template>
  <div class="grid">
    <button
      v-for="o in safeItems"
      :key="o.uid"
      class="card"
      :class="{ nodata: !o.hasData }"
      @click="$emit('select', o.uid)"
      :disabled="!o.hasData"
      type="button"
    >
      <div class="top">
        <div class="name">{{ o.name }}</div>
        <RiskBadge v-if="o.hasData" :risk="o.risk" />
        <span v-else class="badge-missing">нема даних</span>
      </div>

      <div class="meta">
        <div v-if="o.hasData">
          Вікно: {{ fmtDateTime(o.from) }} → {{ fmtDateTime(o.to) }}
        </div>
        <div v-else>Для цієї області прогноз не згенеровано.</div>

        <div class="asof">
          Оновлено: {{ o.asOf ? fmtDateTime(o.asOf) : "—" }}
        </div>
      </div>

      <div v-if="o.hasData" class="extras">
        <div class="line">
          Очікувано годин тривоги: <b>{{ fmtHours(o.expectedAlarmHours) }}</b>
        </div>
        <div v-if="o.peaks?.length" class="line peaks">
          Піки:
          <span v-for="p in o.peaks" :key="p.ts" class="peak">
            {{ fmtPeak(p) }}
          </span>
        </div>
      </div>
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { OblastRiskItem, PeakHour } from "../api/types";
import RiskBadge from "./RiskBadge.vue";
import { fmtDateTime } from "../utils/format";

const props = defineProps<{ items: OblastRiskItem[] }>();
defineEmits<{ (e: "select", uid: number): void }>();

const safeItems = computed(() => (Array.isArray(props.items) ? props.items : []));

function fmtHours(v: number | null) {
  if (v == null || Number.isNaN(v)) return "—";
  return v.toFixed(2);
}

function fmtPeak(p: PeakHour) {
  // peak hour item in UI: { ts, pAlarm }
  const dt = fmtDateTime(p.ts);
  const pct = Math.round((p.pAlarm ?? 0) * 100);
  return ${dt} (${pct}%);
}
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.card {
  text-align: left;
  background: white;
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  display: grid;
  gap: 10px;
}

.card:hover {
  border-color: #cfcfcf;
}

.card:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card.nodata {
  background: #fafafa;
}

.top {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
}

.name {
  font-weight: 600;
  line-height: 1.2;
}

.badge-missing {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid #ddd;
  color: #777;
  white-space: nowrap;
}

.meta {
  font-size: 12px;
  color: #555;
  display: grid;
  gap: 6px;
}

.asof {
  color: #777;
}

.extras {
  font-size: 12px;
  color: #444;
  display: grid;
  gap: 6px;
}

.peaks {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.peak {
  background: #f3f3f3;
  border-radius: 999px;
  padding: 2px 8px;
}
</style>