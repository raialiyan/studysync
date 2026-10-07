function TaskCard({ title, status }) {
    return (
      <div className="card">
        <h3>{title}</h3>
        <p>Status: {status}</p>
      </div>
    )
  }
  
  export default TaskCard