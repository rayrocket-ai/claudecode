<template>
  <div class="min-h-full flex items-center justify-center py-12 px-4">
    <div class="max-w-md w-full">
      <div class="text-center mb-8">
        <div class="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center mx-auto mb-4">
          <span class="text-white font-bold text-lg">RP</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Create your account</h1>
        <p class="text-sm text-gray-500 mt-1">Save searches, track favorites, and get alerts</p>
      </div>

      <form @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
          <input v-model="name" type="text" required autocomplete="name"
            class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="email" type="email" required autocomplete="email"
            class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input v-model="password" type="password" required autocomplete="new-password" minlength="8"
            class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Confirm Password</label>
          <input v-model="passwordConfirmation" type="password" required autocomplete="new-password"
            class="w-full border border-gray-300 rounded-lg px-3 py-2.5 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none" />
        </div>

        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

        <button type="submit" :disabled="submitting"
          class="w-full bg-primary-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors">
          {{ submitting ? 'Creating account...' : 'Create Account' }}
        </button>
      </form>

      <p class="text-center text-sm text-gray-500 mt-6">
        Already have an account?
        <router-link to="/login" class="text-primary-600 hover:text-primary-700 font-medium">Sign in</router-link>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const name = ref('')
const email = ref('')
const password = ref('')
const passwordConfirmation = ref('')
const error = ref('')
const submitting = ref(false)

async function handleRegister() {
  error.value = ''
  if (password.value !== passwordConfirmation.value) {
    error.value = 'Passwords do not match'
    return
  }
  submitting.value = true
  try {
    await authStore.register(name.value, email.value, password.value, passwordConfirmation.value)
    router.push('/')
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } } }
    error.value = err.response?.data?.message || 'Registration failed'
  } finally {
    submitting.value = false
  }
}
</script>
