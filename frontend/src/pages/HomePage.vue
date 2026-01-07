<template>
  <div class="page">
    <div class="head">
      <h1>Ризик тривоги на 6 годин</h1>
      <div class="sub">Дані — SARIMAX. Клікни область, щоб відкрити деталі.</div>
    </div>

    <div class="controls">
      <div class="left">
        <label class="lbl">Горизонт</label>
        <select v-model.number="horizon">
          <option :value="6">6 год</option>
          <option :value="24">24 год</option>
          <option :value="168">168 год</option>
        </select>
      </div>

      <button class="btn" @click="load" :disabled="loading">
        {{ loading ? "Оновлення..." : "Оновити" }}
      </button>
    </div>

    <div v-if="loading" class="state">Завантаження...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="items.length === 0" class="state">
      Немає даних (можливо, прогноз ще не згенеровано).
    </div>

    <UkraineRiskGrid v-else :items="items" @select="go" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { fetchOblastsRisk } from "../api/api";
import type { OblastRiskItem } from "../api/types";
import UkraineRiskGrid from "../components/UkraineRiskGrid.vue";

const router = useRouter();

const horizon = ref<number>(6);
const items = ref<OblastRiskItem[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

function go(uid: number) {
  router.push(`/oblast/${uid}`);
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const list = await fetchOblastsRisk(horizon.value);
    items.value = Array.isArray(list) ? list : [];
  } catch (e: any) {
    items.value = [];
    error.value = e?.message ?? "Не вдалося завантажити дані";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.head h1 {
  margin: 0;
}
.sub {
  margin-top: 6px;
  color: #666;
  font-size: 14px;
}

.controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 14px 0;
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lbl {
  font-size: 14px;
  color: #333;
}

select {
  padding: 8px 10px;
  border: 1px solid #ddd;
  border-radius: 10px;
  background: white;
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

.state {
  margin-top: 12px;
  color: #666;
  font-size: 14px;
}
.error {
  margin-top: 12px;
  color: #b00020;
}
</style>