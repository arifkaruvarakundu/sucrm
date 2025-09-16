import React from "react";
import clsx from "clsx";

export const Card = React.forwardRef(
  ({ className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx(
        "rounded-2xl border bg-white shadow-sm transition-shadow",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
);

Card.displayName = "Card";

export const CardContent = React.forwardRef(
  ({ className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx("p-4", className)}
      {...props}
    >
      {children}
    </div>
  )
);

CardContent.displayName = "CardContent";
