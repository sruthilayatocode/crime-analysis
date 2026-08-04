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
        <p className="mt-1 text-sm text-gray-400">{profile.role}</p>

        <div className="mt-4 w-full space-y-2 border-t border-gray-800 pt-4 text-left">
          <div className="flex items-center gap-3">
            <svg className="h-4 w-4 shrink-0 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span className="text-sm text-gray-300">{profile.email}</span>
          </div>
          <div className="flex items-center gap-3">
            <svg className="h-4 w-4 shrink-0 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span className="text-sm text-gray-300">{profile.phone}</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

export default UserProfileCard