export default function IncidentCard({ incident, onOpen }) {
  const owner =
    typeof incident.owner === "object"
      ? incident.owner?.username
      : incident.owner;

  return (
    <button
      type="button"
      className={`incident-card priority-${(incident.priority || "").toLowerCase()}`}
      onClick={() => onOpen(incident.id)}
    >
      <div className="incident-card-heading">
        <strong>
          <span className="incident-id">#{incident.id}</span> {incident.title}
        </strong>

        <span
          className={`priority-pill ${(incident.priority || "").toLowerCase()}`}
        >
          {incident.priority}
        </span>
      </div>

      <div className="incident-card-meta">
        <span>
          ◷{" "}
          {incident.created_at
            ? new Date(incident.created_at).toLocaleString()
            : "Incident"}
        </span>

        <span>♙ Owner: {owner || "Unassigned"}</span>
      </div>
      <span className="card-arrow">›</span>
    </button>
  );
}
