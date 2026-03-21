<template>
  <router-link
    :to="{ name: 'property', params: { id: property.id } }"
    class="block bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
    @mouseenter="$emit('hover', property.id)"
    @mouseleave="$emit('hover', null)"
  >
    <!-- Image -->
    <div class="relative h-40 bg-gray-200">
      <img
        v-if="property.photos?.[0]"
        :src="property.photos[0]"
        :alt="property.short_address || address"
        class="w-full h-full object-cover"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-gray-400 text-sm">
        No Photo
      </div>

      <!-- Status badge -->
      <span
        :class="['absolute top-2 left-2 px-2 py-0.5 rounded text-xs font-medium',
          property.status === 'sold' ? 'bg-red-600 text-white' : 'bg-green-600 text-white']"
      >
        {{ property.status === 'sold' ? 'SOLD' : 'FOR SALE' }}
      </span>

      <!-- Days on market -->
      <span v-if="property.days_on_market != null" class="absolute top-2 right-2 bg-black/60 text-white px-2 py-0.5 rounded text-xs">
        {{ property.days_on_market }}d
      </span>
    </div>

    <!-- Info -->
    <div class="p-3">
      <p class="text-lg font-bold text-gray-900">
        {{ formatPrice(displayPrice) }}
        <span v-if="property.status === 'sold' && property.sold_to_list_ratio" class="text-xs font-normal text-gray-500 ml-1">
          ({{ property.sold_to_list_ratio }}% of ask)
        </span>
      </p>
      <p class="text-sm text-gray-600 mt-0.5">{{ address }}</p>
      <div class="flex items-center gap-3 mt-2 text-xs text-gray-500">
        <span>{{ property.bedrooms }} bed</span>
        <span>{{ property.bathrooms }} bath</span>
        <span v-if="property.sqft_range || property.interior_sqft">
          {{ formatSqft(property.sqft_range || property.interior_sqft) }}
        </span>
        <span class="ml-auto text-gray-400">{{ formatPropertyType(property.property_type) }}</span>
      </div>
    </div>
  </router-link>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatPrice, formatSqft, formatPropertyType } from '@/utils/formatters'
import type { Property } from '@/types'

const props = defineProps<{ property: Property }>()

defineEmits<{ hover: [id: number | null] }>()

const address = computed(() => {
  const p = props.property
  let addr = `${p.street_number} ${p.street_name}`
  if (p.unit_number) addr = `#${p.unit_number} - ${addr}`
  return `${addr}, ${p.city}`
})

const displayPrice = computed(() =>
  props.property.status === 'sold' && props.property.sold_price
    ? props.property.sold_price
    : props.property.list_price
)
</script>
