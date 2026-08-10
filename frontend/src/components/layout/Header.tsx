type HeaderProps = {
  title: string
  subtitle: string
}

export function Header({ title, subtitle }: HeaderProps) {
  return (
    <header>
      <h1 className="text-2xl font-bold tracking-tight text-foreground">{title}</h1>
      <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>
    </header>
  )
}
