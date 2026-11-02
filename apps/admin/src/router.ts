import { createRouter, createWebHashHistory } from "vue-router";

export type AdminSection =
  | "tutorials"
  | "community"
  | "reminder-settings"
  | "reminders"
  | "logs";

const routes = [
  { path: "/login", name: "login", component: () => import("./components/LoginView.vue") },
  { path: "/codex-watch/tutorials", name: "tutorials", component: () => import("./components/AdminDashboard.vue"), meta: { section: "tutorials" } },
  { path: "/codex-watch/community", name: "community", component: () => import("./components/AdminDashboard.vue"), meta: { section: "community" } },
  { path: "/codex-watch/reminder-settings", name: "reminder-settings", component: () => import("./components/AdminDashboard.vue"), meta: { section: "reminder-settings" } },
  { path: "/ops/reminders", name: "reminders", component: () => import("./components/AdminDashboard.vue"), meta: { section: "reminders" } },
  { path: "/ops/request-logs", name: "logs", component: () => import("./components/AdminDashboard.vue"), meta: { section: "logs" } },
  { path: "/", redirect: "/codex-watch/tutorials" },
  { path: "/:pathMatch(.*)*", redirect: "/codex-watch/tutorials" },
];

export const router = createRouter({
  history: createWebHashHistory(),
  routes,
});
