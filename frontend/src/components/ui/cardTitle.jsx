import React from "react";
import clsx from "clsx";

const CardTitle = React.forwardRef(
  ({ className = "", children, ...props }, ref) => (
    <h2
      ref={ref}
      className={clsx("text-xl font-semibold text-slate-800", className)}
      {...props}
    >
      {children}
    </h2>
  )
);

CardTitle.displayName = "CardTitle";

export default CardTitle;
