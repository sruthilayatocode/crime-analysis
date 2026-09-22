const API_BASE_URL = 'http://127.0.0.1:5000/api'

export async function getCrimes() {
  const response = await fetch(`${API_BASE_URL}/crimes`)

  if (!response.ok) {
    throw new Error('Failed to fetch crimes')
  }

  return response.json()
}

export async function getStatistics() {
  const response = await fetch(`${API_BASE_URL}/crimes/statistics`)

  if (!response.ok) {
    throw new Error('Failed to fetch statistics')
  }

  return response.json()
}

export async function getHotspots() {
  const response = await fetch(`${API_BASE_URL}/hotspots`)

  if (!response.ok) {
    throw new Error('Failed to fetch hotspots')
  }

  return response.json()
}

export async function getNearbyCrimes(latitude, longitude, radius = 5) {
  const response = await fetch(
    `${API_BASE_URL}/crimes/nearby?latitude=${latitude}&longitude=${longitude}&radius=${radius}`
  )

  if (!response.ok) {
    throw new Error('Failed to fetch nearby crimes')
  }

  return response.json()
}

export async function checkProximity(latitude, longitude, alertRadius = 500) {
  const response = await fetch(`${API_BASE_URL}/proximity-check`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      latitude,
      longitude,
      alert_radius_meters: alertRadius,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to check proximity')
  }

  return response.json()
}

export async function getLocationRisk(location) {
  const response = await fetch(
    `${API_BASE_URL}/risk/${encodeURIComponent(location)}`
  )

  if (!response.ok) {
    throw new Error('Failed to fetch location risk')
  }

  return response.json()
}

export async function checkBackendHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)

  if (!response.ok) {
    throw new Error('Backend is not healthy')
  }

  return response.json()
}

// ---- Authentication -----------------------------------------

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function requestJson(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)

  let payload = null

  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const error = new Error(
      payload?.message || `Request failed with status ${response.status}`
    )

    error.status = response.status
    error.details = payload?.details ?? null

    throw error
  }

  return payload
}

export async function loginUser(email, password) {
  return requestJson('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
}

export async function registerUser({ name, email, password }) {
  return requestJson('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password }),
  })
}

export async function fetchCurrentUser(token) {
  return requestJson('/auth/me', { headers: authHeaders(token) })
}

export async function logoutUser(token) {
  return requestJson('/auth/logout', {
    method: 'POST',
    headers: authHeaders(token),
  })
}

export async function getUsers(token) {
  return requestJson('/users', { headers: authHeaders(token) })
}

export async function updateUserRole(userId, role, token) {
  return requestJson(`/users/${userId}/role`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(token),
    },
    body: JSON.stringify({ role }),
  })
}

