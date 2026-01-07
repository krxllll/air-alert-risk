<template>
  <div class="app">
    <AppHeader />
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppHeader from "./components/AppHeader.vue";
</script>

<style>
.app { min-height: 100vh; display: flex; flex-direction: column; }
.main { width: 100%; max-width: 1200px; margin: 0 auto; padding: 16px; }
</style>
