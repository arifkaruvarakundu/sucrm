import { Navigate, Outlet } from "react-router-dom";

// Mock authentication check
// Replace this with your real auth logic (e.g., check JWT in localStorage)
const useAuth = () => {
  const token = localStorage.getItem("token");
  return !!token; 
};

const ProtectedRoute = () => {
  const isAuth = useAuth();

  return isAuth ? <Outlet /> : <Navigate to="/" replace />;
};

export default ProtectedRoute;
