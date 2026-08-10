import type { Activity } from '../../../types/api'
import { activityIcon } from '../activityIcons'

type ActivityItemProps = {
  activity: Activity
  isLast?: boolean
}

export function ActivityItem({ activity, isLast = false }: ActivityItemProps) {
  const { text, time, kind } = activity
  const Icon = activityIcon(kind)

  return (
    <li className="relative flex gap-3">
      {!isLast && (
        <span
          className="absolute top-9 left-4 h-[calc(100%-1.25rem)] w-px bg-border"
          aria-hidden="true"
        />
      )}

      <div className="relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50 text-primary">
        <Icon size={14} />
      </div>

      <div className="min-w-0 pb-5">
        <p className="text-sm leading-snug text-foreground">{text}</p>
        <p className="mt-1 text-xs text-muted-foreground">{time}</p>
      </div>
    </li>
  )
}
