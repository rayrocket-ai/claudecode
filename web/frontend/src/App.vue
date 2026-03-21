<template>
  <div id="app" class="h-screen flex flex-col">
    <AppHeader />
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
</script>
