import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-gradient-to-r from-cyan-500/20 to-violet-500/20 text-cyan-400 shadow-sm',
        secondary:
          'border-transparent bg-secondary/80 backdrop-blur-sm text-secondary-foreground',
        destructive:
          'border-transparent bg-destructive/20 backdrop-blur-sm text-destructive',
        outline:
          'border-border text-muted-foreground hover:border-accent/50 hover:text-accent',
        success:
          'border-transparent bg-success/20 backdrop-blur-sm text-success',
        warning:
          'border-transparent bg-warning/20 backdrop-blur-sm text-warning',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
