import { useCallback, useEffect, useMemo, useState } from 'react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Card from '../components/Card'
import CardHeader from '../components/CardHeader'
import DataTable from '../components/DataTable'
import SearchBar from '../components/SearchBar'
import { useAuth } from '../hooks/useAuth'
import { getUsers, updateUserRole } from '../services/api'
import { ROLES, normalizeRole } from '../utils/roles'

const pillStyles = {
  [ROLES.ADMIN]: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
  [ROLES.USER]: 'bg-gray-500/10 text-gray-300 border-gray-500/30',
}

function ManageUsers() {
  const { token, user: currentUser } = useAuth()

  const [accounts, setAccounts] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [savingId, setSavingId] = useState(null)

  const loadAccounts = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const result = await getUsers(token)
      setAccounts(result.data ?? [])
    } catch (loadError) {
      setError(loadError.message || 'Unable to load accounts.')
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadAccounts()
  }, [loadAccounts])

  const handleRoleChange = async (account) => {
    const currentRole = normalizeRole(account.role)
    const nextRole = currentRole === ROLES.ADMIN ? ROLES.USER : ROLES.ADMIN

    setSavingId(account.id)
    setError('')

    try {
      const updated = await updateUserRole(account.id, nextRole, token)

      setAccounts((previous) =>
        previous.map((entry) => (entry.id === account.id ? updated.data : entry))
      )
    } catch (saveError) {
      setError(saveError.message || 'Unable to update the account role.')
    } finally {
      setSavingId(null)
    }
  }

  const filteredAccounts = useMemo(() => {
    if (!searchTerm) return accounts

    const term = searchTerm.toLowerCase()

    return accounts.filter(
      (account) =>
        account.name?.toLowerCase().includes(term) ||
        account.email?.toLowerCase().includes(term) ||
        account.role?.toLowerCase().includes(term)
    )
  }, [accounts, searchTerm])

  const adminCount = accounts.filter(
    (account) => normalizeRole(account.role) === ROLES.ADMIN
  ).length

  const columns = [
    { key: 'name', label: 'Name', cellClassName: 'font-medium text-gray-200' },
    { key: 'email', label: 'Email', cellClassName: 'text-gray-400' },
    {
      key: 'role',
      label: 'Role',
      render: (account) => (
        <span
          className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${
            pillStyles[normalizeRole(account.role)]
          }`}
        >
          {normalizeRole(account.role)}
        </span>
      ),
    },
    {
      key: 'created_at',
      label: 'Created',
      cellClassName: 'text-gray-500',
      render: (account) => (account.created_at ? account.created_at.slice(0, 10) : '-'),
    },
    {
      key: 'actions',
      label: 'Action',
      render: (account) => {
        const isSelf = account.id === currentUser?.id

        return (
          <button
            type="button"
            disabled={isSelf || savingId === account.id}
            onClick={() => handleRoleChange(account)}
            className="rounded-lg bg-gray-800 px-3 py-1.5 text-xs font-medium text-gray-300 transition-colors hover:bg-gray-700 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isSelf
              ? 'Current account'
              : normalizeRole(account.role) === ROLES.ADMIN
                ? 'Make USER'
                : 'Make ADMIN'}
          </button>
        )
      },
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Manage Users"
        description="Administrator-only view of every CrimeSense account and its role."
        badge={
          <div className="rounded-lg bg-gray-800/50 px-4 py-2">
            <p className="text-xs text-gray-500">Total Accounts</p>
            <p className="text-sm font-medium text-gray-300">{accounts.length}</p>
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          id="total"
          label="Total Accounts"
          value={accounts.length}
          change="+1"
          trend="up"
          color="blue"
        />
        <StatCard
          id="admins"
          label="Administrators"
          value={adminCount}
          change="0"
          trend="down"
          color="red"
        />
        <StatCard
          id="users"
          label="Standard Users"
          value={accounts.length - adminCount}
          change="+1"
          trend="down"
          color="green"
        />
      </div>

      <Card>
        <div className="mb-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <CardHeader title="Accounts" subtitle="Role changes take effect immediately" />
          <div className="w-full lg:max-w-sm">
            <SearchBar
              value={searchTerm}
              onChange={setSearchTerm}
              placeholder="Search by name, email or role..."
            />
          </div>
        </div>

        {error && (
          <p className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-400">
            {error}
          </p>
        )}

        {loading ? (
          <p className="py-8 text-center text-sm text-gray-500">Loading accounts...</p>
        ) : (
          <DataTable
            columns={columns}
            data={filteredAccounts}
            emptyMessage="No accounts match your search."
          />
        )}
      </Card>
    </div>
  )
}

export default ManageUsers
