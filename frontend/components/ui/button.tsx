import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]',
  {
    variants: {
      variant: {
        default:
          'bg-gradient-to-br from-cyan-500 to-violet-600 text-white shadow-md hover:shadow-lg hover:shadow-violet-500/25 hover:from-cyan-400 hover:to-violet-500',
        destructive:
          'bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90',
        outline:
          'border border-border bg-background/50 backdrop-blur-sm shadow-sm hover:bg-accent/10 hover:border-accent/50 hover:text-accent-foreground',
        secondary:
          'bg-secondary/80 backdrop-blur-sm text-secondary-foreground shadow-sm hover:bg-secondary/60',
        ghost:
          'hover:bg-accent/10 hover:text-accent-foreground',
        link:
          'text-primary underline-offset-4 hover:underline',
        gradient:
          'bg-gradient-to-r from-amber-500 via-rose-500 to-pink-500 text-white shadow-md hover:shadow-lg hover:shadow-rose-500/25',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-lg px-3 text-xs',
        lg: 'h-11 rounded-xl px-8 text-base',
        icon: 'h-9 w-9',
        'icon-lg': 'h-11 w-11',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button, buttonVariants }
