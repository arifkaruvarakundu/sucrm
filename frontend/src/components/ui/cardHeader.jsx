import React from "react";
import clsx from "clsx";

const CardHeader = React.forwardRef(
  ({ className = "", children, ...props }, ref) => (
    <div
      ref={ref}
      className={clsx("px-4 py-3 border-b bg-slate-50 rounded-t-2xl", className)}
      {...props}
    >
      {children}
    </div>
  )
);

CardHeader.displayName = "CardHeader";

export default CardHeader;
