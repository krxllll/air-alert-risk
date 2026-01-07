import type { RouteRecordRaw } from "vue-router";
import HomePage from "../pages/HomePage.vue";
import OblastPage from "../pages/OblastPage.vue";

const routes: RouteRecordRaw[] = [
  { path: "/", name: "home", component: HomePage },
  { path: "/oblast/:uid", name: "oblast", component: OblastPage, props: true }
];

export default routes;
