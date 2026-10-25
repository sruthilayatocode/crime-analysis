import React, { useState, useEffect, useCallback } from 'react';
import {
  Users,
  Search,
  Shield,
  UserCheck,
  UserX,
  Trash2,
  MapPin,
  Star,
  ChevronRight,
  ChevronLeft,
  X,
  Radio,
  Eye,
  Activity,
  AlertTriangle,
  Lock,
  RefreshCw,
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { adminService } from '../../services/adminService';

const userMarkerIcon = (zone = 'green') => {
  const color = zone === 'red' ? '#ef4444' : zone === 'yellow' || zone === 'orange' ? '#f59e0b' : '#10b981';
  return L.divIcon({
    className: 'custom-user-marker',
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 6px ${color};"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
};

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [perPage, setPerPage] = useState(15);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');

  // User detail drawer modal
  const [selectedUserDetail, setSelectedUserDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [toastMsg, setToastMsg] = useState('');

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await adminService.getUsers({
        page,
        per_page: perPage,
        q: search,
        role: roleFilter,
      });
      setUsers(res.users || []);
      setTotal(res.total || 0);
      setPages(res.pages || 1);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, perPage, search, roleFilter]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 4000);
  };

  const handleInspectUser = async (userId) => {
    setLoadingDetail(true);
    setSelectedUserDetail(null);
    try {
      const res = await adminService.getUserDetail(userId);
      setSelectedUserDetail(res);
    } catch (err) {
      alert(err.message || 'Failed to load user details');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleToggleActive = async (u) => {
    const nextStatus = !u.is_active;
    try {
      await adminService.toggleUserActive(u.id, nextStatus);
      showToast(`User ${u.name} account ${nextStatus ? 'activated' : 'deactivated'}.`);
      fetchUsers();
      if (selectedUserDetail && selectedUserDetail.user.id === u.id) {
        setSelectedUserDetail({
          ...selectedUserDetail,
          user: { ...selectedUserDetail.user, is_active: nextStatus },
        });
      }
    } catch (err) {
      alert(err.message || 'Failed to change user status');
    }
  };

  const handleChangeRole = async (u) => {
    const newRole = u.role === 'admin' ? 'user' : 'admin';
    if (window.confirm(`Change role of '${u.name}' to ${newRole.toUpperCase()}?`)) {
      try {
        await adminService.changeUserRole(u.id, newRole);
        showToast(`User role updated to ${newRole}.`);
        fetchUsers();
        if (selectedUserDetail && selectedUserDetail.user.id === u.id) {
          setSelectedUserDetail({
            ...selectedUserDetail,
            user: { ...selectedUserDetail.user, role: newRole },
          });
        }
      } catch (err) {
        alert(err.message || 'Failed to change role');
      }
    }
  };

  const handleDeleteUser = async (u) => {
    if (window.confirm(`Permanently DELETE user '${u.name}' (${u.email}) and all personal data? This cannot be undone.`)) {
      try {
        await adminService.deleteUser(u.id);
        showToast(`User '${u.email}' removed permanently.`);
        if (selectedUserDetail && selectedUserDetail.user.id === u.id) {
          setSelectedUserDetail(null);
        }
        fetchUsers();
      } catch (err) {
        alert(err.message || 'Failed to delete user');
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-white">Citizen & User Management</h1>
            <span className="text-[10px] font-bold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-800">
              {total} Registered Users
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Manage user accounts, monitor location consent, inspect safety contacts and distress history
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchUsers}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700 flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {toastMsg && (
        <div className="p-3 bg-emerald-950/90 border border-emerald-700 text-emerald-200 rounded-xl text-xs flex items-center gap-2">
          <UserCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search by user name or email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500"
          />
        </div>

        <div className="w-full sm:w-48">
          <select
            value={roleFilter}
            onChange={(e) => {
              setRoleFilter(e.target.value);
              setPage(1);
            }}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-red-500"
          >
            <option value="all">All Roles (User & Admin)</option>
            <option value="user">Citizens (User)</option>
            <option value="admin">Administrators</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 font-bold border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">User</th>
                <th className="py-3.5 px-4">Role</th>
                <th className="py-3.5 px-4">Account Status</th>
                <th className="py-3.5 px-4">Location Sharing</th>
                <th className="py-3.5 px-4">Last Zone</th>
                <th className="py-3.5 px-4">SOS Contacts</th>
                <th className="py-3.5 px-4">Signed Up</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-red-500" />
                    Loading user registry...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No matching users found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-xl bg-red-800 text-white font-bold flex items-center justify-center text-xs shrink-0">
                          {u.name ? u.name[0].toUpperCase() : 'U'}
                        </div>
                        <div>
                          <span className="font-bold text-white block">{u.name}</span>
                          <span className="text-[11px] text-slate-400 block">{u.email}</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block text-[10px] font-black px-2 py-0.5 rounded-full ${
                          u.role === 'admin'
                            ? 'bg-blue-950 text-blue-400 border border-blue-800'
                            : 'bg-slate-800 text-slate-300'
                        }`}
                      >
                        {u.role.toUpperCase()}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          u.is_active
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-red-950 text-red-400 border border-red-800'
                        }`}
                      >
                        {u.is_active ? 'Active' : 'Deactivated'}
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      {u.location_sharing_enabled ? (
                        <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1">
                          <Radio className="w-3 h-3 text-emerald-400 animate-pulse" />
                          <span>Enabled {u.share_live_location_with_admin ? '(Admin Allowed)' : '(Private)'}</span>
                        </span>
                      ) : (
                        <span className="text-[11px] text-slate-500 font-medium">Disabled</span>
                      )}
                    </td>

                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-block text-[10px] font-black px-2 py-0.5 rounded-full ${
                          u.last_known_zone === 'red'
                            ? 'bg-red-950 text-red-400 border border-red-800'
                            : u.last_known_zone === 'orange' || u.last_known_zone === 'yellow'
                            ? 'bg-amber-950 text-amber-400 border border-amber-800'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}
                      >
                        {u.last_known_zone.toUpperCase()}
                      </span>
                    </td>

                    <td className="py-3.5 px-4 font-mono font-bold text-slate-300">
                      {u.sos_contact_count} / 5
                    </td>

                    <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                      {u.created_at ? u.created_at.slice(0, 10) : 'N/A'}
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          type="button"
                          onClick={() => handleInspectUser(u.id)}
                          className="p-1.5 text-slate-400 hover:text-cyan-400 hover:bg-slate-800 rounded-lg transition-colors"
                          title="Inspect User Details & Map Trail"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleActive(u)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            u.is_active
                              ? 'text-slate-400 hover:text-amber-400 hover:bg-slate-800'
                              : 'text-amber-400 hover:text-emerald-400 hover:bg-slate-800'
                          }`}
                          title={u.is_active ? 'Deactivate account' : 'Activate account'}
                        >
                          {u.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleChangeRole(u)}
                          className="p-1.5 text-slate-400 hover:text-blue-400 hover:bg-slate-800 rounded-lg transition-colors"
                          title="Change role"
                        >
                          <Shield className="w-4 h-4" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteUser(u)}
                          className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-lg transition-colors"
                          title="Permanently delete user"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <span>
            Page {page} of {pages}
          </span>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              type="button"
              disabled={page >= pages}
              onClick={() => setPage(page + 1)}
              className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ===================================================================== */}
      {/* USER DETAIL INSPECTION DRAWER MODAL                                   */}
      {/* ===================================================================== */}
      {selectedUserDetail && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 space-y-4 shadow-2xl text-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-red-700 text-white font-bold flex items-center justify-center text-base">
                  {selectedUserDetail.user.name ? selectedUserDetail.user.name[0].toUpperCase() : 'U'}
                </div>
                <div>
                  <h3 className="text-base font-bold text-white leading-tight">{selectedUserDetail.user.name}</h3>
                  <p className="text-xs text-slate-400">{selectedUserDetail.user.email}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedUserDetail(null)}
                className="text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Quick stats banner */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-500 block">Role</span>
                <span className="font-bold text-white uppercase">{selectedUserDetail.user.role}</span>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-500 block">Status</span>
                <span className={`font-bold ${selectedUserDetail.user.is_active ? 'text-emerald-400' : 'text-red-400'}`}>
                  {selectedUserDetail.user.is_active ? 'Active' : 'Deactivated'}
                </span>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-500 block">SOS Contacts</span>
                <span className="font-bold text-white">{selectedUserDetail.contacts?.length || 0}</span>
              </div>
              <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] text-slate-500 block">Saved Places</span>
                <span className="font-bold text-white">{selectedUserDetail.saved_locations?.length || 0}</span>
              </div>
            </div>

            {/* SOS Contacts section */}
            <div className="space-y-2">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-red-500" />
                <span>Registered SOS Emergency Contacts</span>
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {(selectedUserDetail.contacts || []).map((c) => (
                  <div key={c.id} className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-xs space-y-0.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white">{c.name}</span>
                      {c.is_primary && (
                        <span className="text-[9px] font-black text-red-400 bg-red-950 px-1.5 py-0.2 rounded border border-red-800">
                          Primary
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-400 font-mono">{c.phone}</p>
                    <span className="text-[10px] text-slate-500">{c.relationship}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Location History Trail Map */}
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-cyan-400" />
                  <span>GPS Location History Trail</span>
                </span>
                {!selectedUserDetail.location_sharing_consented && (
                  <span className="text-[10px] text-amber-400 bg-amber-950 px-2 py-0.5 rounded border border-amber-800">
                    Location sharing restricted by user privacy
                  </span>
                )}
              </div>

              {selectedUserDetail.location_history && selectedUserDetail.location_history.length > 0 ? (
                <div className="h-52 rounded-xl overflow-hidden border border-slate-800">
                  <MapContainer
                    center={[
                      selectedUserDetail.location_history[0].latitude,
                      selectedUserDetail.location_history[0].longitude,
                    ]}
                    zoom={14}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      attribution="&copy; OpenStreetMap"
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    {selectedUserDetail.location_history.map((l, idx) => (
                      <Marker key={idx} position={[l.latitude, l.longitude]} icon={userMarkerIcon(l.zone)}>
                        <Popup>
                          <div className="text-xs text-slate-900">
                            <strong>{l.recorded_at}</strong>
                            <p>Zone: {l.zone}</p>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                    <Polyline
                      positions={selectedUserDetail.location_history.map((l) => [l.latitude, l.longitude])}
                      color="#06b6d4"
                      weight={3}
                      opacity={0.7}
                    />
                  </MapContainer>
                </div>
              ) : (
                <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 text-center text-xs text-slate-500">
                  {selectedUserDetail.location_sharing_consented
                    ? 'No recent location history pings recorded for this user.'
                    : 'Location tracking disabled in user personal privacy settings.'}
                </div>
              )}
            </div>

            {/* SOS Events History */}
            <div className="space-y-2 pt-2">
              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
                <span>Distress SOS Events History</span>
              </span>

              {selectedUserDetail.sos_events && selectedUserDetail.sos_events.length > 0 ? (
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {selectedUserDetail.sos_events.map((e) => (
                    <div key={e.id} className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 text-xs flex items-center justify-between">
                      <div>
                        <span className="font-bold text-white block">
                          SOS #{e.id} ({e.type})
                        </span>
                        <span className="text-[10px] text-slate-400 block">{e.created_at}</span>
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          e.status === 'active'
                            ? 'bg-red-950 text-red-400 border border-red-800 animate-pulse'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}
                      >
                        {e.status.toUpperCase()}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-500 bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                  No emergency SOS distress events recorded for this user.
                </p>
              )}
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedUserDetail(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-bold"
              >
                Close Drawer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
