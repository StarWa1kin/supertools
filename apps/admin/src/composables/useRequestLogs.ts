import { ref } from "vue";

import { ApiError, getRequestLogs } from "../api";
import type { RequestLogPage, RequestLogQuery } from "../types";

export function useRequestLogs(token: () => string, clearSession: () => void) {
  const logs = ref<RequestLogPage>({ total: 0, items: [] });
  const loading = ref(false);

  async function load(query: RequestLogQuery = {}) {
    loading.value = true;
    try {
      logs.value = await getRequestLogs(token(), query);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) clearSession();
      throw error;
    } finally {
      loading.value = false;
    }
  }

  return { logs, loading, load };
}
