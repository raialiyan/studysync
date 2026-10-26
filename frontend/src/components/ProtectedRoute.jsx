
import { Navigate, Outlet } from "react-router-dom";
import { getToken } from "../api";

function ProtectedRoute() {
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

export default ProtectedRoute;
