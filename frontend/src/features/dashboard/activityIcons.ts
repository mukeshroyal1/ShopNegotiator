import type { LucideIcon } from 'lucide-react'
import {
  CheckCircle2,
  MessageCircle,
  Package,
  Search,
  Send,
  Sparkles,
} from 'lucide-react'

const kindIcons: Record<string, LucideIcon> = {
  search: Search,
  send: Send,
  message: MessageCircle,
  completed: CheckCircle2,
  package: Package,
  system: Sparkles,
}

export function activityIcon(kind: string): LucideIcon {
  return kindIcons[kind] ?? Sparkles
}
