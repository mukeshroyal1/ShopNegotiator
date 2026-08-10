import type { Activity } from '../../../types/api'
import { ActivityItem } from './ActivityItem'

type RecentActivityProps = {
  activities: Activity[]
}

export function RecentActivity({ activities }: RecentActivityProps) {
  return (
    <section>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-foreground">Recent Activity</h2>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Latest AI actions and updates
        </p>
      </div>

      <div className="rounded-xl border border-border bg-card p-5 shadow-soft">
        {activities.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No activity yet. Negotiations and AI actions will show up here.
          </p>
        ) : (
          <ul className="m-0 list-none p-0">
            {activities.map((activity, index) => (
              <ActivityItem
                key={activity.id}
                activity={activity}
                isLast={index === activities.length - 1}
              />
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
