import TaskCard from '../components/TaskCard'

function Tasks() {
  return (
    <div>
      <h2>Tasks</h2>

      <TaskCard title="Finish database schema" status="In Progress" />
      <TaskCard title="Revise neural networks" status="Not Started" />
    </div>
  )
}

export default Tasks