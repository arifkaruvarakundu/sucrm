import { Navigate, Outlet } from "react-router-dom";
import { useSelector } from "react-redux";

const ProtectedRoute = () => {
  // Access isAuthenticated from Redux store
  const isAuth = useSelector((state) => state.AuthReducer.isAuthenticated);

  return isAuth ? <Outlet /> : <Navigate to="/" replace />;
};

export default ProtectedRoute;
