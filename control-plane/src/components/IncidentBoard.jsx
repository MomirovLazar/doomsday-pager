import IncidentCard from "./IncidentCard";

export default function IncidentBoard({ incidents, onOpenIncident }) {
  const columns = [
    { title: "NEW INCIDENTS", status: "NEW" },
    { title: "IN PROGRESS", status: "IN_PROGRESS" },
    { title: "RESOLVED", status: "RESOLVED" },
  ];

  return (
    <div className="incident-board">
      {columns.map((column) => {
        const items = incidents.filter((item) => item.status === column.status);

        return (
          <div
            className={`incident-column column-${column.status.toLowerCase()}`}
            key={column.status}
          >
            <div className="column-heading">
              <h3>
                <i />
                {column.title}
              </h3>

              <span>{items.length}</span>
            </div>

            <div className="incident-list">
              {items.map((item) => (
                <IncidentCard
                  key={item.id}
                  incident={item}
                  onOpen={onOpenIncident}
                />
              ))}

              {items.length === 0 && (
                <p className="empty-column">No incidents</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
