<template>
  <div class="wrap">
    <div class="hint">
      <div class="title">Карта України (опційно)</div>
      <div class="sub">
        Додай SVG у <code>public/maps/ukraine-oblasts.svg</code>.
        Кожна область має мати <code>id="uid-14"</code>, <code>id="uid-27"</code> і т.д.
      </div>
    </div>

    <div v-if="available" class="map">
      <object ref="obj" type="image/svg+xml" :data="src" @load="onLoad" />
    </div>

    <div v-else class="fallback">
      SVG не знайдено — використовуй сітку нижче.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { OblastRiskItem } from "../api/types";
import { clamp01 } from "../utils/format";

const props = defineProps<{ items: OblastRiskItem[] }>();
const emit = defineEmits<{ (e: "select", uid: number): void }>();

const src = "/maps/ukraine-oblasts.svg";
const available = ref(true);
const obj = ref<HTMLObjectElement | null>(null);

function paint(svgDoc: Document) {
  for (const it of props.items) {
    const el = svgDoc.getElementById(`uid-${it.uid}`);
    if (!el) continue;

    const r = it.risk == null ? 0 : clamp01(it.risk);
    const fill = it.hasData
      ? r >= 0.7 ? "#ff8a8a" : r >= 0.4 ? "#ffd38a" : "#a8d5ff"
      : "#e6e6e6";

    (el as any).style.fill = fill;
    (el as any).style.cursor = it.hasData ? "pointer" : "default";
    (el as any).style.transition = "opacity 120ms ease";

    el.replaceWith(el.cloneNode(true));
  }

  for (const it of props.items) {
    if (!it.hasData) continue;
    const el = svgDoc.getElementById(`uid-${it.uid}`);
    if (!el) continue;
    el.addEventListener("click", () => emit("select", it.uid));
    el.addEventListener("mouseenter", () => ((el as any).style.opacity = "0.85"));
    el.addEventListener("mouseleave", () => ((el as any).style.opacity = "1"));
  }
}

async function onLoad() {
  const svgDoc = obj.value?.contentDocument;
  if (!svgDoc) {
    available.value = false;
    return;
  }
  paint(svgDoc);
}

watch(
  () => props.items,
  () => {
    const svgDoc = obj.value?.contentDocument;
    if (svgDoc) paint(svgDoc);
  },
  { deep: true }
);

fetch(src)
  .then((r) => { if (!r.ok) available.value = false; })
  .catch(() => { available.value = false; });
</script>

<style scoped>
.wrap { border: 1px solid #e6e6e6; border-radius: 12px; padding: 12px; background: white; }
.hint .title { font-weight: 600; }
.hint .sub { font-size: 12px; color: #666; margin-top: 4px; }
.map { margin-top: 10px; }
object { width: 100%; height: 520px; border: none; }
.fallback { margin-top: 10px; font-size: 12px; color: #777; }
code { background: #f3f3f3; padding: 1px 4px; border-radius: 6px; }
</style>
