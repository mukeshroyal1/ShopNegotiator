import { LogOut } from 'lucide-react'
import { useAuth } from '../../features/auth/AuthProvider'

function getInitials(nameOrEmail: string) {
  const value = nameOrEmail.trim()
  if (!value) return '?'
  if (value.includes(' ')) {
    return value
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? '')
      .join('')
  }
  return value.slice(0, 2).toUpperCase()
}

export function UserProfile() {
  const { user, signOut } = useAuth()
  const fullName =
    (user?.user_metadata?.full_name as string | undefined)?.trim() || ''
  const email = user?.email ?? ''
  const displayName = fullName || email || 'Account'
  const initials = getInitials(fullName || email)

  return (
    <div className="border-t border-sidebar-border px-4 py-4">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary text-xs font-semibold text-primary-foreground">
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-foreground">
            {displayName}
          </p>
          {fullName && email ? (
            <p className="truncate text-xs text-muted-foreground">{email}</p>
          ) : null}
        </div>
      </div>

      <button
        type="button"
        onClick={() => void signOut()}
        className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-border bg-card px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
      >
        <LogOut size={14} />
        Sign out
      </button>
    </div>
  )
}
