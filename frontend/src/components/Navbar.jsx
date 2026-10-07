import { Link } from 'react-router-dom'

function Navbar() {
  return (
    <header>
      <h1>StudySync</h1>

      <nav>
        <Link to="/">Dashboard</Link>
        <Link to="/workspaces">Workspaces</Link>
        <Link to="/tasks">Tasks</Link>
        <Link to="/login">Login</Link>
        <Link to="/register">Register</Link>
      </nav>
    </header>
  )
}

export default Navbar