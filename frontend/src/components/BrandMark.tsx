import { Link } from 'react-router-dom'

type BrandMarkProps = {
  to?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const heights = {
  sm: 'h-8',
  md: 'h-10',
  lg: 'h-16 md:h-20',
} as const

const logoFrameClassName =
  'rounded-xl border-2 border-white bg-white object-contain shadow-soft'

export function BrandMark({
  to = '/',
  size = 'md',
  className = '',
}: BrandMarkProps) {
  const content = (
    <span className={`inline-flex items-center gap-2.5 no-underline ${className}`}>
      <img
        src="/BargainLabs.png"
        alt="Bargain Labs"
        className={`${heights[size]} w-auto max-w-[280px] ${logoFrameClassName}`}
      />
    </span>
  )

  if (!to) return content
  return (
    <Link to={to} className="no-underline">
      {content}
    </Link>
  )
}
