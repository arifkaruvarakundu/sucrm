import React from "react";
import clsx from "clsx";

const CardContent = React.forwardRef(
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

export default CardContent;
