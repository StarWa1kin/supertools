import { onBeforeUnmount, ref } from "vue";

import { ApiError, getDeploymentStatus, startDeployment } from "../api";
import type { DeploymentStatus } from "../types";

const initial: DeploymentStatus = {
  status: "idle",
  startedAt: null,
  finishedAt: null,
  log: "",
  targets: {
    server: { version: null, deployedAt: null },
    admin: { version: null, deployedAt: null },
  },
};

export function useDeployment(token: () => string, onUnauthorized: () => void) {
  const deployment = ref<DeploymentStatus>({ ...initial });
  const loadingDeployment = ref(false);
  let timer: number | undefined;

  function stopPolling() {
    if (timer) window.clearTimeout(timer);
    timer = undefined;
  }

  async function loadDeployment() {
    if (!token()) return;
    try {
      deployment.value = await getDeploymentStatus(token());
      if (deployment.value.status === "running") {
        stopPolling();
        timer = window.setTimeout(() => {
          loadDeployment().catch(() => {
            timer = window.setTimeout(() => void loadDeployment().catch(stopPolling), 3000);
          });
        }, 2000);
      } else {
        stopPolling();
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) onUnauthorized();
      throw error;
    }
  }

  async function deploy(target: "server" | "admin") {
    loadingDeployment.value = true;
    try {
      deployment.value = await startDeployment(token(), target);
      await loadDeployment();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) onUnauthorized();
      throw error;
    } finally {
      loadingDeployment.value = false;
    }
  }

  onBeforeUnmount(stopPolling);
  return { deployment, loadingDeployment, loadDeployment, deploy };
}
