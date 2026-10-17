import Card from './Card'

function UserProfileCard({ profile }) {
  return (
    <Card className="flex items-center justify-center">
      <div className="flex flex-col items-center text-center">
        {/* Avatar placeholder */}
        <div className="relative">
          <div className="flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 text-3xl font-bold text-white shadow-lg">
            {profile.initials}
          </div>
          <span className="absolute bottom-0 right-0 flex h-6 w-6 items-center justify-center rounded-full border-2 border-gray-900 bg-green-500">
            <svg className="h-3 w-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
            </svg>
          </span>
        </div>

        <h2 className="mt-4 text-xl font-bold text-white">{profile.name}</h2>
        <span className="mt-1 inline-flex items-center gap-1.5 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-0.5 text-xs font-semibold text-blue-400">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400" />
          {profile.role}
        </span>

        <div className="mt-4 w-full space-y-2.5 border-t border-gray-800 pt-4 text-left">
          <div className="flex items-center gap-3">
            <svg className="h-4 w-4 shrink-0 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span className="text-xs sm:text-sm text-gray-300 truncate">{profile.email}</span>
          </div>
          <div className="flex items-center gap-3">
            <svg className="h-4 w-4 shrink-0 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V8a2 2 0 00-2-2h-5m-4 0V5a2 2 0 114 0v1m-4 0a2 2 0 104 0m-5 8a2 2 0 100-4 2 2 0 000 4zm0 0c1.306 0 2.417.835 2.83 2M9 14a3.001 3.001 0 00-2.83 2M15 11h3m-3 4h2" />
            </svg>
            <span className="text-xs sm:text-sm text-gray-400 font-mono">
              Account ID: {profile.userId ? `#${profile.userId}` : 'Verified Session'}
            </span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default UserProfileCard