import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Workspaces from './pages/Workspaces'
import Tasks from './pages/Tasks'
import Login from './pages/Login'
import Register from './pages/Register'


import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <Navbar />

      <main>
         
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route element={<ProtectedRoute />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/workspaces" element={<Workspaces />} />
              <Route path="/tasks" element={<Tasks />} />
            </Route>
          </Routes>

      </main>
    </BrowserRouter>
  )
}

export default App