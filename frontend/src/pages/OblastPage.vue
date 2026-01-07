<template>
  <div class="page">
    <div class="top">
      <h1>Деталі по області</h1>
      <button class="btn" @click="load" :disabled="loading">
        {{ loading ? "Оновлення..." : "Оновити" }}
      </button>
    </div>

    <div class="card">
      <div class="row">
        <label>Область</label>
        <select v-model.number="selectedUid" @change="onSelect">
          <option v-for="o in oblastOptions" :key="o.uid" :value="o.uid">
            {{ o.name }}
          </option>
        </select>
      </div>

      <div class="meta" v-if="risk">
        <div class="line">
          <b>UID:</b> {{ risk.uid }}
        </div>
        <div class="line">
          <b>Модель:</b> {{ risk.modelVersion }}
        </div>
        <div class="line" v-if="risk.generatedAt">
          <b>Згенеровано:</b> {{ fmtDateTime(risk.generatedAt) }}
        </div>
        <div class="line">
          <b>Горизонт:</b> {{ fmtDateTime(risk.from) }} → {{ fmtDateTime(risk.to) }}
        </div>

        <div class="line" v-if="status">
          <b>Статус зараз:</b>
          <span :class="`st-${status.status}`">{{ statusLabel(status.status) }}</span>
        </div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="risk" class="cards">
      <div class="mini" v-for="w in windows" :key="w.hours">
        <div class="k">{{ w.hours }} год</div>
        <RiskBadge :risk="w.riskAny" />
        <div class="small">
          {{ fmtDateTime(w.from) }} → {{ fmtDateTime(w.to) }}
        </div>
        <div class="small" v-if="w.expectedAlarmHours != null">
          Очікувано годин тривоги: {{ w.expectedAlarmHours.toFixed(2) }}
        </div>
      </div>
    </div>

    <div v-if="risk" style="margin-top: 12px">
      <HourlyForecastChart :hourly="risk.hourly" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import { fetchOblastRisk, fetchOblastsList, fetchStatuses } from "../api/api";
import type { OblastRiskResponse, StatusItem, UaOblast } from "../api/types";

import RiskBadge from "../components/RiskBadge.vue";
import HourlyForecastChart from "../components/HourlyForecastChart.vue";

import { fmtDateTime, statusLabel } from "../utils/format";
import { detectDefaultOblastUid } from "../utils/geo";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const error = ref<string | null>(null);

const selectedUid = ref<number>(Number(route.params.uid ?? 14));

const risk = ref<OblastRiskResponse | null>(null);
const status = ref<StatusItem | null>(null);

const oblastOptions = ref<UaOblast[]>([]);

async function loadOblastOptions() {
  oblastOptions.value = await fetchOblastsList();
}

async function loadStatus(uid: number) {
  try {
    const s = await fetchStatuses();
    const found = s.items.find((x) => x.uid === uid) ?? null;
    status.value = found;
  } catch {
    status.value = null;
  }
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const uid = selectedUid.value;

    risk.value = await fetchOblastRisk(uid, { horizons: "1,6,24,168", seriesHours: 168 });
    await loadStatus(uid);
  } catch (e: any) {
    error.value = e?.message ?? "Не вдалося завантажити деталі";
    risk.value = null;
    status.value = null;
  } finally {
    loading.value = false;
  }
}

async function onSelect() {
  router.replace(`/oblast/${selectedUid.value}`);
  await load();
}

watch(
  () => route.params.uid,
  async (v) => {
    const uid = Number(v);
    if (!Number.isNaN(uid) && uid !== selectedUid.value) {
      selectedUid.value = uid;
      await load();
    }
  }
);

const windows = computed(() => {
  const r = risk.value;
  if (!r) return [];

  const series = r.series ?? [];
  const summaries = r.summary ?? {};

  const hoursList = [1, 6, 24, 168];

  return hoursList.map((h) => {
    const key = `h${h}`;
    const s = summaries[key];

    const from = series[0]?.ts ?? r.horizon_start;
    const to = series[Math.min(h, series.length) - 1]?.ts ?? r.horizon_end;

    return {
      hours: h,
      riskAny: s?.risk_any ?? null,
      expectedAlarmHours: s?.expected_alarm_hours ?? null,
      from,
      to,
    };
  });
});

onMounted(async () => {
  try {
    await loadOblastOptions();
  } catch {
    // ok
  }

  if (!route.params.uid) {
    const uid = await detectDefaultOblastUid();
    if (uid) {
      selectedUid.value = uid;
      router.replace(`/oblast/${uid}`);
    }
  }

  await load();
});
</script>

<style scoped>
.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.btn {
  border: 1px solid #ddd;
  background: white;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.6;
  cursor: default;
}

.card {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 12px;
  background: white;
  margin-top: 12px;
}
.row {
  display: grid;
  grid-template-columns: 120px 1fr;
  align-items: center;
  gap: 10px;
}
select {
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
}

.meta {
  margin-top: 12px;
  color: #222;
}
.line {
  margin-top: 6px;
}
.error {
  margin-top: 10px;
  color: #b00020;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.mini {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 12px;
  background: white;
  display: grid;
  gap: 8px;
}
.k {
  font-weight: 600;
}
.small {
  font-size: 12px;
  color: #666;
}

/* status badges */
.st-active {
  color: #b00020;
  font-weight: 600;
}
.st-inactive {
  color: #1b5e20;
  font-weight: 600;
}
.st-unknown {
  color: #555;
  font-weight: 600;
}
</style>
