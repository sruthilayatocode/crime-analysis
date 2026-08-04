export const currentLocation = {
  latitude: 12.9716,
  longitude: 77.5946,
  accuracy: 12.5,
  lastUpdated: '2024-12-15 14:32:45',
}

export const safetyStatus = {
  level: 'Medium Risk',
  message: 'You are within 500m of a medium-risk crime zone. Stay alert and avoid isolated areas.',
}

export const nearestHotspot = {
  name: 'Downtown District',
  crimeType: 'Robbery, Assault',
  distance: 0.42,
  risk: 'High',
}

export const nearbyCrimeSummary = {
  totalCrimes: 87,
  mostCommonCrime: 'Theft',
  lastReported: 'Robbery at Central Park - 12:30 PM',
}

export const locationHistory = [
  { id: 1, time: '14:32:45', latitude: 12.9716, longitude: 77.5946, status: 'Medium Risk' },
  { id: 2, time: '14:27:12', latitude: 12.9721, longitude: 77.5952, status: 'Medium Risk' },
  { id: 3, time: '14:21:38', latitude: 12.9734, longitude: 77.5968, status: 'Safe' },
  { id: 4, time: '14:15:55', latitude: 12.9742, longitude: 77.5981, status: 'Safe' },
  { id: 5, time: '14:10:20', latitude: 12.9751, longitude: 77.5993, status: 'High Risk' },
]