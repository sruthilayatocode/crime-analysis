export const alertSummary = {
  total: 24,
  high: 6,
  medium: 9,
  low: 9,
}

export const recentAlerts = [
  {
    id: 1,
    title: 'High Risk Zone Alert',
    description: 'Suspicious activity detected in Downtown District',
    time: '2 minutes ago',
    location: 'Downtown District',
    priority: 'High',
  },
  {
    id: 2,
    title: 'Proximity Alert',
    description: 'Officer #342 within 100m of high-risk zone',
    time: '15 minutes ago',
    location: 'Northside Avenue',
    priority: 'High',
  },
  {
    id: 3,
    title: 'Crime Spike Detected',
    description: 'Robbery incidents up 25% in Northside Avenue',
    time: '1 hour ago',
    location: 'Northside Avenue',
    priority: 'Medium',
  },
  {
    id: 4,
    title: 'Zone Status Update',
    description: 'Westfield Mall reclassified to High Risk',
    time: '3 hours ago',
    location: 'Westfield Mall',
    priority: 'Medium',
  },
  {
    id: 5,
    title: 'Low Risk Zone Update',
    description: 'Greenwood Estates no longer high-priority',
    time: '5 hours ago',
    location: 'Greenwood Estates',
    priority: 'Low',
  },
  {
    id: 6,
    title: 'System Update',
    description: 'AI model retrained with latest crime data',
    time: '8 hours ago',
    location: 'System',
    priority: 'Low',
  },
]

export const alertHistory = [
  { id: 'AL-2024-001', location: 'Downtown District', crimeType: 'Robbery', time: '2024-12-15 14:32', status: 'Resolved' },
  { id: 'AL-2024-002', location: 'Northside Avenue', crimeType: 'Assault', time: '2024-12-15 13:45', status: 'Active' },
  { id: 'AL-2024-003', location: 'Westfield Mall', crimeType: 'Burglary', time: '2024-12-15 12:20', status: 'Active' },
  { id: 'AL-2024-004', location: 'Central Park', crimeType: 'Vandalism', time: '2024-12-15 11:05', status: 'Resolved' },
  { id: 'AL-2024-005', location: 'Harbor View', crimeType: 'Theft', time: '2024-12-15 10:30', status: 'Pending' },
]

export const emergencyTips = [
  'Stay in well-lit, populated areas, especially at night.',
  'Keep your phone charged and emergency contacts on speed dial.',
  'Avoid isolated routes; use main roads with more traffic.',
  'Report suspicious activity immediately to local authorities.',
  'Share your live location with trusted family or friends.',
]