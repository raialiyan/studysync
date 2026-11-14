import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import Workspaces from './pages/Workspaces';
import Tasks from './pages/Tasks';
import Login from './pages/Login';
import Register from './pages/Register';
import './App.css';
function Shell(){
  const {pathname}=useLocation();
  const auth=pathname==='/login'||pathname==='/register';
  return <div className={auth?'auth-shell':'app-shell'}>{!auth&&<Navbar/>}<main className={auth?'auth-main':'app-main'}><Routes>
    <Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/>
    <Route element={<ProtectedRoute/>}><Route path="/" element={<Dashboard/>}/><Route path="/workspaces" element={<Workspaces/>}/><Route path="/tasks" element={<Tasks/>}/></Route>
    <Route path="*" element={<Navigate to="/" replace/>}/>
  </Routes></main></div>
}
export default function App(){return <BrowserRouter><Shell/></BrowserRouter>}
