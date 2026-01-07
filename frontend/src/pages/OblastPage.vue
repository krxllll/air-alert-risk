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

      <div v-if="meta" class="meta">
        <div class="name"><b>{{ meta.name }}</b></div>
        <div class="status">
          Статус зараз:
          <b :class="`st-${meta.nowStatus}`">{{ statusLabel(meta.nowStatus) }}</b>
        </div>
        <div class="asof">Прогноз згенеровано: {{ meta.generatedAt ? fmtDateTime(meta.generatedAt) : "—" }}</div>
        <div class="asof">Покриття: {{ fmtDateTime(meta.from) }} → {{ fmtDateTime(meta.to) }}</div>
      </div>

      <div v-if="error" class="error">{{ error }}</div>
    </div>

    <div v-if="meta" class="cards">
      <div class="mini" v-for="w in meta.windows" :key="w.hours">
        <div class="k">{{ w.hours }} год</div>
        <RiskBadge :risk="w.risk" />
        <div class="small">{{ fmtDateTime(w.from) }} → {{ fmtDateTime(w.to) }}</div>
        <div class="small">
          Очікувано годин тривоги: <b>{{ w.expectedAlarmHours.toFixed(2) }}</b>
        </div>
      </div>
    </div>

    <div v-if="meta" style="margin-top: 12px">
      <HourlyForecastChart :hourly="meta.hourly" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { fetchOblastRisk, fetchOblastsList, fetchStatuses } from "../api/api";
import type {
  HourlyPoint,
  OblastRiskResponse,
  OblastRiskWindow,
  PeakHour,
  StatusItem,
  UaOblast
} from "../api/types";
import { detectDefaultOblastUid } from "../utils/geo";
import { fmtDateTime, statusLabel } from "../utils/format";
import RiskBadge from "../components/RiskBadge.vue";
import HourlyForecastChart from "../components/HourlyForecastChart.vue";

const route = useRoute();
const router = useRouter();

const loading = ref(false);
const error = ref<string | null>(null);

const selectedUid = ref<number>(Number(route.params.uid ?? 14));
const oblastOptions = ref<UaOblast[]>([]);

const meta = ref<OblastRiskResponse | null>(null);

function findName(uid: number): string {
  return oblastOptions.value.find(o => o.uid === uid)?.name ?? `uid=${uid}`;
}

async function loadOptions() {
  oblastOptions.value = await fetchOblastsList();
}

async function load() {
  loading.value = true;
  error.value = null;

  try {
    const api = await fetchOblastRisk(selectedUid.value, {
      horizons: "1,6,24,168",
      seriesHours: 168
    });

    const st = await fetchStatuses();
    const now = st.items.find(x => x.uid === selectedUid.value)?.status ?? "unknown";

    const hourly: HourlyPoint[] = (api.series ?? []).map(p => ({
      ts: p.ts,
      p: p.p_alarm
    }));

    const windows: OblastRiskWindow[] = Object.entries(api.summary ?? {})
      .map(([k, v]) => {
        const hours = Number(k.replace(/^h/, ""));
        const end = pickWindowEnd(api.horizon_start, hours);
        return {
          hours,
          risk: v.risk_any,
          expectedAlarmHours: v.expected_alarm_hours,
          peaks: (v.peak_hours ?? []).map((p: any) => ({ ts: p.ts, pAlarm: p.p_alarm })) as PeakHour[],
          from: api.horizon_start,
          to: end
        };
      })
      .filter(w => Number.isFinite(w.hours))
      .sort((a, b) => a.hours - b.hours);

    meta.value = {
      uid: api.oblast_uid,
      modelVersion: api.model_version,
      generatedAt: api.generated_at,
      name: findName(api.oblast_uid),
      nowStatus: now as StatusItem["status"] | "unknown",
      from: api.horizon_start,
      to: api.horizon_end,
      hourly,
      windows
    };
  } catch (e: any) {
    meta.value = null;
    error.value = e?.message ?? "Не вдалося завантажити деталі";
  } finally {
    loading.value = false;
  }
}

function pickWindowEnd(horizonStart: string, hours: number): string {
  const d = new Date(horizonStart);
  d.setUTCHours(d.getUTCHours() + Math.max(0, hours - 1));
  return d.toISOString();
}

function onSelect() {
  router.replace(`/oblast/${selectedUid.value}`);
  load();
}

watch(
  () => route.params.uid,
  (v) => {
    const uid = Number(v);
    if (!Number.isNaN(uid) && uid !== selectedUid.value) {
      selectedUid.value = uid;
      load();
    }
  }
);

onMounted(async () => {
  try {
    await loadOptions();
  } catch {
    // ignore
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
  background: white;
}

.meta {
  margin-top: 12px;
  color: #222;
  display: grid;
  gap: 6px;
}

.status {
  font-size: 14px;
}

.asof {
  font-size: 12px;
  color: #777;
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

.st-active {
  color: #b00020;
}
.st-inactive {
  color: #0b6b2b;
}
.st-unknown {
  color: #666;
}
</style>
