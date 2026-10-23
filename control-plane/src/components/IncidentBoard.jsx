import IncidentCard from "./IncidentCard";

export default function IncidentBoard({ incidents, onOpenIncident }) {
  const columns = [
    {
      title: "NEW",
      items: incidents.filter((incident) => incident.status === "NEW"),
    },
    {
      title: "IN PROGRESS",
      items: incidents.filter((incident) => incident.status === "IN_PROGRESS"),
    },
    {
      title: "RESOLVED",
      items: incidents.filter((incident) => incident.status === "RESOLVED"),
    },
  ];

  return (
    <div className="incident-board">
      {columns.map((column) => (
        <div className="incident-column" key={column.title}>
          <h3>
            {column.title} ({column.items.length})
          </h3>

          <div className="incident-list">
            {column.items.map((incident) => (
              <IncidentCard
                key={incident.id}
                incident={incident}
                onOpen={onOpenIncident}
              />
            ))}

            {column.items.length === 0 && (
              <p className="empty-column">No incidents</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
