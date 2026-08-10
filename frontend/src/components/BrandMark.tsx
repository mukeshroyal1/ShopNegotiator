import { Link } from 'react-router-dom'

type BrandMarkProps = {
  to?: string
  size?: 'sm' | 'md' | 'lg'
  showWordmark?: boolean
  className?: string
}

const heights = {
  sm: 'h-8',
  md: 'h-10',
  lg: 'h-16 md:h-20',
} as const

/** Shared frame: rounded corners + white border around the logo image. */
export const brandLogoFrameClassName =
  'rounded-xl border-2 border-white bg-white object-contain shadow-soft'

export function BrandMark({
  to = '/',
  size = 'md',
  showWordmark = false,
  className = '',
}: BrandMarkProps) {
  const content = (
    <span className={`inline-flex items-center gap-2.5 no-underline ${className}`}>
      <img
        src="/BargainLabs.png"
        alt="Bargain Labs"
        className={`${heights[size]} w-auto max-w-[280px] ${brandLogoFrameClassName}`}
      />
      {showWordmark && (
        <span className="text-base font-semibold tracking-tight text-foreground">
          Bargain Labs
        </span>
      )}
    </span>
  )

  if (!to) return content
  return (
    <Link to={to} className="no-underline">
      {content}
    </Link>
  )
}
