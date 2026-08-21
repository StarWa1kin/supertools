<script setup lang="ts">
import { reactive, ref } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import {
  ArrowRight,
  CircleCheckFilled,
  DataAnalysis,
  Lock,
  User,
} from "@element-plus/icons-vue";

defineProps<{ loading: boolean }>();
const emit = defineEmits<{
  submit: [payload: { username: string; password: string }];
}>();

const formRef = ref<FormInstance>();
const form = reactive({ username: "admin", password: "" });
const rules: FormRules = {
  username: [{ required: true, message: "请输入账号", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
};

async function submit() {
  if (!(await formRef.value?.validate().catch(() => false))) return;
  emit("submit", { ...form });
}
</script>

<template>
  <main class="login-page">
    <div class="login-canvas-mark" aria-hidden="true">CODEX</div>

    <header class="login-topbar">
      <div class="login-brand">
        <span class="product-icon"
          ><el-icon><DataAnalysis /></el-icon
        ></span>
        <span><b>Supertools</b><small>Intelligence Console</small></span>
      </div>
      <div class="private-status">
        <CircleCheckFilled /><span>Private workspace</span>
      </div>
    </header>

    <section class="login-stage" aria-label="Codex 情报管理台">
      <div class="login-context">
        <span class="context-eyebrow"><i /> 少一些步骤 快一些答案</span>
        <h1>奇思妙箱</h1>
        <p>管理控制台</p>
        <div class="context-meta">
          <span>SUPERTOOLS</span>
          <span>2026</span>
        </div>
      </div>

      <article class="login-box">
        <div class="login-heading">
          <span class="login-lock"
            ><el-icon><Lock /></el-icon
          ></span>
          <h2>欢迎回来</h2>
          <p>使用管理员账户继续</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="submit"
        >
          <el-form-item label="账号" prop="username">
            <el-input
              v-model="form.username"
              size="large"
              autocomplete="username"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              size="large"
              type="password"
              autocomplete="current-password"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button
            class="login-button"
            native-type="submit"
            :loading="loading"
          >
            <span>{{ loading ? "正在验证..." : "继续" }}</span>
            <el-icon v-if="!loading"><ArrowRight /></el-icon>
          </el-button>
        </el-form>

        <div class="login-note">
          <span><Lock /></span>
          <p>安全会话将在 12 小时后自动失效</p>
        </div>
      </article>
    </section>

    <footer class="login-footer">
      <span>Supertools Operations</span><span>Asia / Shanghai</span>
    </footer>
  </main>
</template>
