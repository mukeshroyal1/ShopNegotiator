import { BrandMark } from '../BrandMark'
import { APP_BASE } from '../../config/navigation'

export function Logo() {
  return (
    <div className="px-4 py-5">
      <BrandMark to={APP_BASE} size="md" />
    </div>
  )
}
