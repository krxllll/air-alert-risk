<template>
  <header class="header">
    <div class="inner">
      <div class="brand">
        <div class="title">Air Alert Risk</div>
        <div class="subtitle">Прогноз ризику тривоги по областях</div>
      </div>

      <nav class="nav">
        <RouterLink to="/">Головна</RouterLink>
        <RouterLink :to="detailsLink">Область</RouterLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const detailsLink = computed(() => {
  const uid = route.params.uid;
  return uid ? `/oblast/${uid}` : `/oblast/14`;
});
</script>

<style scoped>
.header { border-bottom: 1px solid #e6e6e6; background: white; position: sticky; top: 0; z-index: 10; }
.inner { max-width: 1200px; margin: 0 auto; padding: 12px 16px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.brand .title { font-weight: 700; }
.brand .subtitle { font-size: 12px; color: #666; }
.nav { display: flex; gap: 12px; }
.nav a { text-decoration: none; color: #222; padding: 6px 10px; border-radius: 8px; }
.nav a.router-link-active { background: #f3f3f3; }
</style>
