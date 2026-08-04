export const stats = [
  { id: 1, label: 'Total Crimes', value: 1247, change: '+12.5%', trend: 'up', color: 'red' },
  { id: 2, label: 'High Risk Zones', value: 23, change: '+3', trend: 'up', color: 'red' },
  { id: 3, label: 'Medium Risk Zones', value: 47, change: '-2', trend: 'down', color: 'yellow' },
  { id: 4, label: 'Low Risk Zones', value: 89, change: '+5', trend: 'down', color: 'green' },
]

export const crimeTrendData = [
  { month: 'Jan', crimes: 98 },
  { month: 'Feb', crimes: 112 },
  { month: 'Mar', crimes: 87 },
  { month: 'Apr', crimes: 134 },
  { month: 'May', crimes: 121 },
  { month: 'Jun', crimes: 156 },
  { month: 'Jul', crimes: 142 },
  { month: 'Aug', crimes: 168 },
  { month: 'Sep', crimes: 151 },
  { month: 'Oct', crimes: 179 },
  { month: 'Nov', crimes: 165 },
  { month: 'Dec', crimes: 194 },
]

export const recentCrimeReports = [
  { id: 'CR-2024-001', type: 'Robbery', location: 'Downtown District', time: '2024-12-15 14:32', status: 'Under Investigation', risk: 'High' },
  { id: 'CR-2024-002', type: 'Assault', location: 'Northside Avenue', time: '2024-12-15 13:45', status: 'Resolved', risk: 'Medium' },
  { id: 'CR-2024-003', type: 'Burglary', location: 'Westfield Mall', time: '2024-12-15 12:20', status: 'Under Investigation', risk: 'High' },
  { id: 'CR-2024-004', type: 'Vandalism', location: 'Central Park', time: '2024-12-15 11:05', status: 'Resolved', risk: 'Low' },
  { id: 'CR-2024-005', type: 'Theft', location: 'Harbor View', time: '2024-12-15 10:30', status: 'Pending', risk: 'Medium' },
  { id: 'CR-2024-006', type: 'Fraud', location: 'Financial District', time: '2024-12-15 09:15', status: 'Under Investigation', risk: 'High' },
]

export const recentAlerts = [
  { id: 1, title: 'High Risk Zone Alert', message: 'Suspicious activity detected in Downtown District', time: '2 minutes ago', severity: 'critical' },
  { id: 2, title: 'Proximity Alert', message: 'Officer #342 within 100m of high-risk zone', time: '15 minutes ago', severity: 'warning' },
  { id: 3, title: 'Crime Spike Detected', message: 'Robbery incidents up 25% in Northside Avenue', time: '1 hour ago', severity: 'warning' },
  { id: 4, title: 'Zone Status Update', message: 'Westfield Mall reclassified to High Risk', time: '3 hours ago', severity: 'info' },
  { id: 5, title: 'System Update', message: 'AI model retrained with latest crime data', time: '5 hours ago', severity: 'info' },
]