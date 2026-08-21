import { createRouter, createWebHashHistory } from "vue-router";

export type AdminSection =
  | "crawler"
  | "tutorials"
  | "community"
  | "reminders"
  | "logs"
  | "deployment";

const routes = [
  { path: "/login", name: "login", component: () => import("./components/LoginView.vue") },
  { path: "/codex-watch/crawler", name: "crawler", component: () => import("./components/AdminDashboard.vue"), meta: { section: "crawler" } },
  { path: "/codex-watch/tutorials", name: "tutorials", component: () => import("./components/AdminDashboard.vue"), meta: { section: "tutorials" } },
  { path: "/codex-watch/community", name: "community", component: () => import("./components/AdminDashboard.vue"), meta: { section: "community" } },
  { path: "/ops/reminders", name: "reminders", component: () => import("./components/AdminDashboard.vue"), meta: { section: "reminders" } },
  { path: "/ops/request-logs", name: "logs", component: () => import("./components/AdminDashboard.vue"), meta: { section: "logs" } },
  { path: "/ops/deployment", name: "deployment", component: () => import("./components/AdminDashboard.vue"), meta: { section: "deployment" } },
  { path: "/", redirect: "/codex-watch/crawler" },
  { path: "/:pathMatch(.*)*", redirect: "/codex-watch/crawler" },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});
