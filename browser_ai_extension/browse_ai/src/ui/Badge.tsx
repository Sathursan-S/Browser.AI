import * as React from "react"
import { cn } from "../lib/utils"

type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'info' | 'warning' | 'error' | 'success' | 'debug'

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: BadgeVariant
}

const getBadgeClasses = (variant: BadgeVariant = 'default') => {
  const baseClasses = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50"
  
  const variantClasses = {
    default: "border-transparent bg-slate-900 text-slate-50 hover:bg-slate-900/80",
    secondary: "border-transparent bg-slate-100 text-slate-900 hover:bg-slate-100/80",
    destructive: "border-transparent bg-red-500 text-slate-50 hover:bg-red-500/80",
    outline: "text-slate-950 border-white/20",
    info: "border-transparent bg-blue-500/20 text-blue-300 border-blue-500/30",
    warning: "border-transparent bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    error: "border-transparent bg-red-500/20 text-red-300 border-red-500/30",
    success: "border-transparent bg-green-500/20 text-green-300 border-green-500/30",
    debug: "border-transparent bg-gray-500/20 text-gray-300 border-gray-500/30",
  }
  
  return `${baseClasses} ${variantClasses[variant]}`
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  return (
    <div className={cn(getBadgeClasses(variant), className)} {...props} />
  )
}

export { Badge }