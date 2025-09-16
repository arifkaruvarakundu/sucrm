import React from "react";
import clsx from "clsx";

const VARIANTS = {
  default: "bg-slate-800 text-white hover:bg-slate-900",
  ghost: "bg-transparent hover:bg-slate-100/80 text-slate-600 hover:text-slate-800",
};

const SIZES = {
  sm: "px-3 py-1.5 text-sm rounded-md",
  md: "px-4 py-2 text-base rounded-lg",
  lg: "px-6 py-3 text-lg rounded-xl",
};

export const Button = React.forwardRef(
  (
    {
      children,
      className = "",
      variant = "default",
      size = "md",
      type = "button",
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        className={clsx(
          "inline-flex items-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:ring-offset-2 disabled:opacity-60 disabled:pointer-events-none",
          VARIANTS[variant] || VARIANTS.default,
          SIZES[size] || SIZES.md,
          className
        )}
        {...props}
      >
        {children}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
