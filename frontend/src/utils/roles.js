export const ROLES = {
  USER: 'USER',
  ADMIN: 'ADMIN',
}

export const DASHBOARD_PATHS = {
  [ROLES.USER]: '/user/dashboard',
  [ROLES.ADMIN]: '/admin/dashboard',
}

export function normalizeRole(role) {
  if (typeof role !== 'string') return ROLES.USER

  const candidate = role.trim().toUpperCase()

  return candidate in ROLES ? candidate : ROLES.USER
}

export function dashboardPathForRole(role) {
  return DASHBOARD_PATHS[normalizeRole(role)]
}

export function formatRole(role) {
  return normalizeRole(role) === ROLES.ADMIN ? 'System Administrator' : 'Standard User'
}

export function initialsFor(name) {
  if (typeof name !== 'string' || !name.trim()) return 'U'

  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0))
    .join('')
    .toUpperCase()
}
