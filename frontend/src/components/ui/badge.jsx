import React from "react";

export function Badge({ children, className = "", color = "default", ...props }) {
  // color: "default" | "success" | "warning" | "error" | "info"
  const colorClasses = {
    default: "bg-slate-100 text-slate-800 border-slate-200",
    success: "bg-emerald-100 text-emerald-800 border-emerald-200",
    warning: "bg-yellow-100 text-yellow-800 border-yellow-200",
    error: "bg-rose-100 text-rose-800 border-rose-200",
    info: "bg-cyan-100 text-cyan-800 border-cyan-200",
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colorClasses[color] || colorClasses.default} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}

export default Badge;
