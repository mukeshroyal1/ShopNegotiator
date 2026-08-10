import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BrandMark } from '../../components/BrandMark'
import { useAuth } from './AuthProvider'

export function SignUpPage() {
  const { signUp } = useAuth()
  const navigate = useNavigate()

  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setMessage(null)
    setSubmitting(true)

    const result = await signUp(email.trim(), password, fullName.trim())
    setSubmitting(false)

    if (result.error) {
      setError(result.error)
      return
    }

    setMessage(
      'Account created. If email confirmation is enabled in Supabase, check your inbox — otherwise you can sign in now.',
    )
    navigate('/app/connect-shopify', { replace: true })
  }

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden w-1/2 bg-gradient-to-br from-primary/15 via-background to-background lg:block" />

      <div className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <BrandMark to="/" size="md" className="mb-8" />

          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Create your account
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Start negotiating supplier quotes with AI.
          </p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div>
              <label
                htmlFor="fullName"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Full name
              </label>
              <input
                id="fullName"
                type="text"
                autoComplete="name"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                className="h-11 w-full rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/30"
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="h-11 w-full rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/30"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="mb-1.5 block text-sm font-medium text-foreground"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                minLength={6}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="h-11 w-full rounded-xl border border-border bg-card px-3 text-sm text-foreground outline-none focus:ring-2 focus:ring-ring/30"
              />
            </div>

            {error && (
              <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}
            {message && (
              <p className="rounded-lg bg-success/10 px-3 py-2 text-sm text-success">
                {message}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex h-11 w-full items-center justify-center rounded-xl bg-primary text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-60"
            >
              {submitting ? 'Creating account…' : 'Sign up'}
            </button>
          </form>

          <p className="mt-6 text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link
              to="/signin"
              className="font-medium text-primary no-underline hover:text-primary/80"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
