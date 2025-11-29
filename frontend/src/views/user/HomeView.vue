<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const dashboardData = ref(null)
const searchQuery = ref('')
const token = localStorage.getItem('access_token') || ''

const filteredLots = computed(() => {
  if (!dashboardData.value?.available_lots) return []
  const query = searchQuery.value.toLowerCase()
  return dashboardData.value.available_lots.filter(lot =>
    lot.prime_location_name.toLowerCase().includes(query) ||
    lot.address.toLowerCase().includes(query)
  )
})

const userId = localStorage.getItem('user_id')  // or however you store it

const fetchDashboard = async () => {
  try {
    const response = await axios.get(`http://localhost:5000/api/user/dashboard/${userId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
    dashboardData.value = response.data.dashboard
  } catch (error) {
    console.error('Failed to load dashboard:', error)
  }
}

onMounted(fetchDashboard)
</script>

<template>
  <div class="p-6 space-y-6">
    <h2 class="text-2xl font-bold">User Dashboard</h2>

    <div v-if="dashboardData">
      <!-- Section 1: Parking History -->
      <section>
        <h3 class="text-xl font-semibold mb-2">Parking History (Recent)</h3>
        <div v-if="dashboardData.recent_history.length" class="space-y-2">
          <div
            v-for="entry in dashboardData.recent_history"
            :key="entry.id"
            class="p-4 bg-gray-100 rounded shadow"
          >
            <p class="font-medium">Vehicle: {{ entry.vehicle_number }}</p>
            <p>Spot: {{ entry.spot_number }} @ {{ entry.location_name }}</p>
            <p>Status: {{ entry.status }}</p>
            <p>Start: {{ entry.parking_timestamp }}</p>
            <p>End: {{ entry.leaving_timestamp || 'In Progress' }}</p>
            <p>Cost: ₹{{ entry.parking_cost }}</p>
          </div>
        </div>
        <p v-else class="text-gray-500">No recent reservations found.</p>
      </section>

      <!-- Section 2: Search Available Parking Lots -->
      <section>
        <h3 class="text-xl font-semibold mt-6 mb-2">Search Available Parking Lots</h3>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Enter location or address"
          class="border border-gray-300 px-4 py-2 rounded w-full mb-4"
        />
        <div v-if="filteredLots.length" class="space-y-2">
          <div
            v-for="lot in filteredLots"
            :key="lot.id"
            class="p-4 bg-white rounded border shadow"
          >
            <h4 class="text-lg font-bold">{{ lot.prime_location_name }}</h4>
            <p class="text-sm text-gray-600">{{ lot.address }}</p>
            <p>Available Spots: {{ lot.available_spots }} / {{ lot.total_spots }}</p>
            <p>Rate: ₹{{ lot.price }}/hr</p>
            <p>PIN: {{ lot.pin_code }}</p>
          </div>
        </div>
        <p v-else class="text-gray-500">No matching lots found.</p>
      </section>
    </div>

    <div v-else>
      <p>Loading dashboard...</p>
    </div>
  </div>
</template>
