import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../../lib/utils.ts";

const buttonVariants = cva("btn", {
  variants: {
    variant: {
      default: "btn-default",
      chrome: "btn-chrome",
      hot: "btn-hot",
      ghost: "btn-ghost",
    },
    size: {
      default: "btn-size-default",
      sm: "btn-size-sm",
      icon: "btn-size-icon",
    },
  },
  defaultVariants: {
    variant: "default",
    size: "default",
  },
});

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  children: ReactNode;
}

export function Button({ className, variant, size, children, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props}>
      {children}
    </button>
  );
}
