function WorkspaceCard({ name, members }) {
    return (
      <div className="card">
        <h3>{name}</h3>
        <p>{members} members</p>
      </div>
    )
  }
  
  export default WorkspaceCard