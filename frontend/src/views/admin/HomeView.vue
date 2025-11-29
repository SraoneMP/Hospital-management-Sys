<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import axios from 'axios'
import Chart from 'chart.js/auto'
import { useRouter } from 'vue-router'

const router = useRouter()
const token = localStorage.getItem('token') || ''
const authHeader = { Authorization: `Bearer ${token}` }

const loading = ref(true)
const error = ref('')

const overview = ref({
  doctors: 0, patients: 0, appointments: 0, upcoming: 0, completed: 0, cancelled: 0
})
const specializations = ref([])

// Analytics
const range = ref('30d')
const analyticsLoading = ref(false)
const topDoctors = ref([])
const apptByDept = ref([])
const revenueByDept = ref([])

// Chart refs and instances
const deptPieRef = ref(null)
let deptPieChart = null

const revenueBarRef = ref(null)
let revenueBarChart = null

const topDocsBarRef = ref(null)
let topDocsBarChart = null

const destroyCharts = () => {
  if (deptPieChart) { deptPieChart.destroy(); deptPieChart = null }
  if (revenueBarChart) { revenueBarChart.destroy(); revenueBarChart = null }
  if (topDocsBarChart) { topDocsBarChart.destroy(); topDocsBarChart = null }
}
onBeforeUnmount(() => destroyCharts())

const fetchDashboard = async () => {
  const { data } = await axios.get('/api/admin/dashboard', { headers: authHeader })
  overview.value = data.overview || overview.value
  specializations.value = data.specializations || []
}

const palette = (n) => {
  const solidColors = [
    '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
  ]
  const bg = []
  const border = []
  for (let i = 0; i < n; i++) {
    const color = solidColors[i % solidColors.length]
    bg.push(color)
    border.push(color)
  }
  return { bg, border }
}

const renderDeptPie = () => {
  if (!apptByDept.value?.length) return
  const labels = apptByDept.value.map(x => x.department)
  const dataVals = apptByDept.value.map(x => x.appointments)
  const { bg, border } = palette(labels.length)
  const ctx = deptPieRef.value?.getContext('2d')
  if (!ctx) {
    console.warn('Dept pie canvas not ready')
    return
  }
  if (deptPieChart) deptPieChart.destroy()
  deptPieChart = new Chart(ctx, {
    type: 'pie',
    data: {
      labels,
      datasets: [{ label: 'Appointments', data: dataVals, backgroundColor: bg, borderColor: border, borderWidth: 2 }]
    },
    options: { 
      maintainAspectRatio: true,
      plugins: { legend: { position: 'bottom' }, title: { display: true, text: 'Appointments by Department' } } 
    }
  })
}

const renderRevenueBar = () => {
  if (!revenueByDept.value?.length) return
  const labels = revenueByDept.value.map(x => x.department)
  const dataVals = revenueByDept.value.map(x => x.value)
  const { bg, border } = palette(labels.length)
  const ctx = revenueBarRef.value?.getContext('2d')
  if (!ctx) {
    console.warn('Revenue bar canvas not ready')
    return
  }
  if (revenueBarChart) revenueBarChart.destroy()
  revenueBarChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Revenue (₹)', data: dataVals, backgroundColor: bg, borderColor: border, borderWidth: 2, borderRadius: 6 }] },
    options: {
      maintainAspectRatio: false,
      scales: { y: { beginAtZero: true, grid: { color: '#eee' } }, x: { grid: { display: false } } },
      plugins: { legend: { display: false }, title: { display: true, text: 'Top Revenue Departments' },
        tooltip: { callbacks: { label: (ctx) => `₹ ${ctx.parsed.y}` } } }
    }
  })
}

const renderTopDocs = () => {
  if (!topDoctors.value?.length) return
  const labels = topDoctors.value.map(x => x.doctor_name)
  const dataVals = topDoctors.value.map(x => x.bookings)
  const { bg, border } = palette(labels.length)
  const ctx = topDocsBarRef.value?.getContext('2d')
  if (!ctx) {
    console.warn('Top docs bar canvas not ready')
    return
  }
  if (topDocsBarChart) topDocsBarChart.destroy()
  topDocsBarChart = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Bookings', data: dataVals, backgroundColor: bg, borderColor: border, borderWidth: 2, borderRadius: 6 }] },
    options: {
      maintainAspectRatio: true,
      indexAxis: 'y',
      scales: { x: { beginAtZero: true, grid: { color: '#eee' } }, y: { grid: { display: false } } },
      plugins: { legend: { display: false }, title: { display: true, text: 'Top Doctors by Bookings' },
        tooltip: { callbacks: { label: (ctx) => `Bookings: ${ctx.parsed.x}` } } }
    }
  })
}

const renderAllCharts = () => {
  destroyCharts()
  // Use nextTick again to ensure DOM is ready after v-else condition changes
  nextTick(() => {
    renderDeptPie()
    renderRevenueBar()
    renderTopDocs()
  })
}

const fetchAnalytics = async () => {
  analyticsLoading.value = true
  try {
    const { data } = await axios.get('/api/admin/analytics', {
      headers: authHeader, params: { range: range.value }
    })
    topDoctors.value = data.top_doctors || []
    apptByDept.value = data.appointments_by_department || []
    revenueByDept.value = data.revenue_by_department || []
  } finally {
    analyticsLoading.value = false
  }
}

const tileClass = (key) => {
  switch ((key || '').toLowerCase()) {
    case 'cancelled': return 'tile-cancelled'
    case 'completed': return 'tile-completed'
    case 'upcoming': return 'tile-upcoming'
    default: return 'tile-neutral'
  }
}
const labelClass = (key) => {
  switch ((key || '').toLowerCase()) {
    case 'cancelled': return 'text-danger'
    case 'completed': return 'text-success'
    case 'upcoming': return 'text-primary'
    default: return 'text-muted'
  }
}

const isClickableTile = (key) => {
  const clickable = ['cancelled', 'completed', 'upcoming']
  return clickable.includes((key || '').toLowerCase())
}

const handleTileClick = (key) => {
  if (isClickableTile(key)) {
    router.push({ 
      path: '/admin/appointments', 
      query: { status: key.toLowerCase() } 
    })
  }
}

const init = async () => {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([fetchDashboard(), fetchAnalytics()])
  } catch (e) {
    console.error(e)
    error.value = 'Failed to load admin dashboard'
  } finally {
    loading.value = false
    // Render charts after loading state changes and DOM updates
    nextTick(() => {
      renderAllCharts()
    })
  }
}

onMounted(init)
</script>

<template>
  <div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h2 class="mb-0 page-title">Admin Dashboard</h2>
    </div>

    <div v-if="loading" class="alert alert-info">Loading...</div>
    <div v-else-if="error" class="alert alert-danger">{{ error }}</div>

    <div v-else>
      <!-- KPIs -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-4 col-lg-2" v-for="(val, key) in overview" :key="key">
          <div 
            :class="['card', 'shadow-sm', 'h-100', tileClass(key), isClickableTile(key) ? 'clickable-tile' : '']"
            @click="handleTileClick(key)"
            :style="isClickableTile(key) ? 'cursor: pointer;' : ''"
          >
            <div class="card-body">
              <div class="small text-uppercase" :class="labelClass(key)">{{ key.replaceAll('_', ' ') }}</div>
              <div class="fs-3 fw-bold">{{ val }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Specializations table -->
      <div class="card mb-4">
        <div class="card-body">
          <h5 class="mb-2">Doctor Specializations</h5>
          <div class="table-responsive">
            <table class="table table-sm table-striped">
              <thead>
                <tr>
                  <th>Specialization</th>
                  <th>Doctors Count</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in specializations" :key="s.name">
                  <td>{{ s.name }}</td>
                  <td>{{ s.count }}</td>
                </tr>
                <tr v-if="!specializations.length">
                  <td colspan="2" class="text-muted">No data available.</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="form-text">This table helps discover supply by specialization.</div>
        </div>
      </div>

      <!-- Charts -->
      <div class="row g-3">
        <div class="col-12 col-lg-6">
          <div class="card h-100">
            <div class="card-body">
              <canvas ref="deptPieRef" height="150"></canvas>
              <div v-if="!apptByDept.length" class="text-muted small mt-2">No department data in selected range.</div>
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-6">
          <div class="card h-100">
            <div class="card-body">
              <canvas ref="topDocsBarRef" height="150"></canvas>
              <div v-if="!topDoctors.length" class="text-muted small mt-2">No doctor activity in selected range.</div>
            </div>
          </div>
        </div>

        <div class="col-12">
          <div class="card h-100">
            <div class="card-body">
              <div style="height: 200px;">
                <canvas ref="revenueBarRef"></canvas>
              </div>
              <div v-if="!revenueByDept.length" class="text-muted small mt-2">No completed appointments in selected range.</div>
              <div class="form-text">Revenue = Sum of consultation fees from completed visits (by department).</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.container { max-width: 1200px; }
.fs-3 { font-size: 1.75rem; }

/* Tile color hints */
.tile-cancelled .card-body { background: #fee2e2; }  /* red-100 */
.tile-completed .card-body { background: #dcfce7; }  /* green-100 */
.tile-upcoming .card-body  { background: #dbeafe; }  /* blue-100 */
.tile-neutral .card-body   { background: #f8fafc; }  /* slate-50 */

/* Clickable tiles */
.clickable-tile {
  transition: transform 0.2s, box-shadow 0.2s;
}

.clickable-tile:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

.clickable-tile:active {
  transform: translateY(-1px);
}
</style>
