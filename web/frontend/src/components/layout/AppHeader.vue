<template>
  <header class="bg-white border-b border-gray-200 h-14 flex items-center px-4 z-50 shrink-0">
    <!-- Logo -->
    <router-link to="/" class="flex items-center gap-2 mr-6">
      <div class="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
        <span class="text-white font-bold text-sm">RP</span>
      </div>
      <span class="text-lg font-semibold text-gray-900 hidden sm:block">Realty Platform</span>
    </router-link>

    <!-- Search bar -->
    <div class="flex-1 max-w-xl">
      <SearchBar />
    </div>

    <!-- Nav -->
    <nav class="flex items-center gap-3 ml-4">
      <router-link
        v-if="authStore.isAuthenticated"
        to="/favorites"
        class="text-gray-600 hover:text-primary-600 text-sm font-medium hidden md:block"
      >
        Favorites
      </router-link>
      <router-link
        v-if="authStore.isAuthenticated"
        to="/saved-searches"
        class="text-gray-600 hover:text-primary-600 text-sm font-medium hidden md:block"
      >
        Saved Searches
      </router-link>

      <!-- Auth buttons -->
      <template v-if="!authStore.isAuthenticated">
        <router-link
          to="/login"
          class="text-gray-600 hover:text-primary-600 text-sm font-medium"
        >
          Log In
        </router-link>
        <router-link
          to="/register"
          class="bg-primary-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
        >
          Sign Up
        </router-link>
      </template>

      <!-- User menu -->
      <template v-else>
        <div class="relative" ref="menuRef">
          <button
            @click="showMenu = !showMenu"
            class="flex items-center gap-2 text-sm text-gray-700 hover:text-primary-600"
          >
            <div class="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center font-semibold">
              {{ authStore.user?.name?.charAt(0).toUpperCase() }}
            </div>
          </button>
          <div
            v-if="showMenu"
            class="absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50"
          >
            <div class="px-4 py-2 border-b border-gray-100">
              <p class="text-sm font-medium text-gray-900">{{ authStore.user?.name }}</p>
              <p class="text-xs text-gray-500">{{ authStore.user?.email }}</p>
            </div>
            <router-link to="/dashboard" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" @click="showMenu = false">
              Dashboard
            </router-link>
            <router-link to="/favorites" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" @click="showMenu = false">
              Favorites
            </router-link>
            <router-link to="/saved-searches" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50" @click="showMenu = false">
              Saved Searches
            </router-link>
            <button
              @click="handleLogout"
              class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
            >
              Log Out
            </button>
          </div>
        </div>
      </template>
    </nav>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { onClickOutside } from '@vueuse/core'
import { useAuthStore } from '@/store/auth'
import SearchBar from '@/components/search/SearchBar.vue'

const authStore = useAuthStore()
const router = useRouter()
const showMenu = ref(false)
const menuRef = ref<HTMLElement>()

onClickOutside(menuRef, () => { showMenu.value = false })

async function handleLogout() {
  showMenu.value = false
  await authStore.logout()
  router.push('/')
}
</script>
