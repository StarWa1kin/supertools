<script setup lang="ts">
import { useTheme, type ThemeName } from "../composables/useTheme";

const { options, setTheme, theme } = useTheme();

function chooseTheme(name: ThemeName) {
  if (theme.value !== name) setTheme(name);
}
</script>

<template>
  <view class="theme-switcher" aria-label="外观主题">
    <button
      v-for="option in options"
      :key="option.name"
      class="theme-option"
      :class="{ 'theme-option--active': theme === option.name }"
      :aria-label="`${option.label}主题`"
      :aria-pressed="theme === option.name"
      @click="chooseTheme(option.name)"
    >
      <view
        class="theme-option__swatch"
        :style="{ backgroundColor: option.swatch }"
        aria-hidden="true"
      >
        <text v-if="theme === option.name" class="theme-option__check">✓</text>
      </view>
    </button>
  </view>
</template>

<style scoped>
.theme-switcher {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.theme-option {
  display: flex;
  width: 56rpx;
  height: 56rpx;
  min-height: 0;
  margin: 0;
  padding: 0;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: var(--color-ink);
  line-height: 1;
  transition: transform 120ms ease-out, opacity 120ms ease-out;
}

.theme-option::after {
  border: 0;
}

.theme-option:active {
  transform: scale(0.88);
  opacity: 0.72;
}

.theme-option__swatch {
  display: flex;
  width: 34rpx;
  height: 34rpx;
  flex: 0 0 34rpx;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-soft-border);
  border-radius: 50%;
  box-shadow: 0 2rpx 6rpx var(--color-shadow-soft);
}

.theme-option--active {
  box-shadow: inset 0 0 0 1px var(--color-border);
}

.theme-option__check {
  color: #ffffff;
  font-size: 18rpx;
  font-weight: 800;
  line-height: 1;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.42);
}

@media (prefers-reduced-motion: reduce) {
  .theme-option {
    transition: none;
  }
}
</style>
