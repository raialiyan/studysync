import WorkspaceCard from '../components/WorkspaceCard'

function Workspaces() {
  return (
    <div>
      <h2>Workspaces</h2>

      <WorkspaceCard name="COMP3000 Project" members={4} />
      <WorkspaceCard name="Machine Learning Revision" members={3} />
    </div>
  )
}

export default Workspaces