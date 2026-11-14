import { NavLink, useNavigate } from 'react-router-dom';
import { logout } from '../api';
const links=[['/','Overview','▦'],['/workspaces','Workspaces','▤'],['/tasks','Task board','☷']];
export default function Navbar(){const navigate=useNavigate();return <>
  <aside className="sidebar"><NavLink to="/" className="brand" aria-label="StudySync home"><span className="brand-symbol">✳</span><span>study<span className="brand-emphasis">sync</span><small>YOUR COLLABORATIVE SPACE</small></span></NavLink>
    <div className="side-caption">WORKSPACE</div><nav className="side-nav" aria-label="Primary navigation">{links.map(([to,label,icon])=><NavLink key={to} end={to==='/'} to={to} className={({isActive})=>'side-link'+(isActive?' active':'')}><span className="nav-glyph" aria-hidden="true">{icon}</span>{label}<span className="nav-arrow">›</span></NavLink>)}</nav>
    <div className="sidebar-bottom"><div className="sidebar-tip"><span className="sidebar-tip-icon">✦</span><strong>Better together.</strong><span>Plan your study sessions, track progress and keep everyone in sync.</span></div><button className="signout" onClick={()=>{logout();navigate('/login',{replace:true})}}><span aria-hidden="true">↪</span> Sign out</button></div>
  </aside><header className="mobile-header"><NavLink to="/" className="mobile-brand">✳ <b>studysync</b></NavLink><nav aria-label="Mobile navigation">{links.map(([to,label])=><NavLink end={to==='/'} key={to} to={to}>{label}</NavLink>)}</nav><button onClick={()=>{logout();navigate('/login',{replace:true})}}>↪</button></header>
</>}
