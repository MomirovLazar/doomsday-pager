export default function IncidentCard({ incident, onOpen }) {
  return (
    <button
      type="button"
      className="incident-card"
      onClick={() => onOpen(incident.id)}
    >
      <strong>{incident.title}</strong>
      <span>#{incident.id}</span>
      <span>Priority: {incident.priority}</span>
    </button>
  );
}
