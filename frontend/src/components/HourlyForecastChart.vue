<template>
  <div class="card">
    <div class="title">Погодинний прогноз (p_alarm)</div>

    <div v-if="!hourly || hourly.length === 0" class="empty">
      Немає даних для графіка
    </div>

    <div v-else class="chart">
      <Line :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ApiRiskSeriesPoint } from "../api/types";

import { Line } from "vue-chartjs";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
);

const props = defineProps<{
  hourly: ApiRiskSeriesPoint[];
}>();

function clamp01(x: number) {
  if (Number.isNaN(x)) return 0;
  return Math.max(0, Math.min(1, x));
}

const labels = computed(() =>
  (props.hourly ?? []).map((p) =>
    new Date(p.ts).toLocaleString(undefined, {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  )
);

const values = computed(() =>
  (props.hourly ?? []).map((p) => clamp01(p.p_alarm))
);

const chartData = computed(() => ({
  labels: labels.value,
  datasets: [
    {
      label: "p_alarm",
      data: values.value,
      tension: 0.25,
      pointRadius: 0,
      borderWidth: 2,
      fill: false,
    },
  ],
}));

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index" as const, intersect: false },
  plugins: {
    legend: { display: true },
    tooltip: { enabled: true },
  },
  scales: {
    y: { min: 0, max: 1 },
  },
}));
</script>

<style scoped>
.card {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 12px;
  background: white;
}
.title {
  font-weight: 600;
  margin-bottom: 10px;
}
.chart {
  height: 320px;
}
.empty {
  font-size: 12px;
  color: #777;
  padding: 8px 0;
}
</style>