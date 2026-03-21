import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/on/toronto-real-estate/map',
    },
    {
      path: '/on/:city-real-estate/map',
      name: 'map',
      component: () => import('@/views/MapView.vue'),
      meta: { title: 'Map Search' },
    },
    {
      path: '/property/:id',
      name: 'property',
      component: () => import('@/views/PropertyView.vue'),
      meta: { title: 'Property Details' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { title: 'Login', guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { title: 'Register', guest: true },
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: 'Dashboard', requiresAuth: true },
    },
    {
      path: '/favorites',
      name: 'favorites',
      component: () => import('@/views/FavoritesView.vue'),
      meta: { title: 'Favorites', requiresAuth: true },
    },
    {
      path: '/saved-searches',
      name: 'saved-searches',
      component: () => import('@/views/SavedSearchesView.vue'),
      meta: { title: 'Saved Searches', requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router
