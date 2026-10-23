import IncidentBoard from "../components/IncidentBoard";

export default function DashboardPage({
  incidents,
  search,
  onSearchChange,
  loading,
  error,
  onOpenIncident,
}) {
  const searchText = search.toLowerCase().trim();

  const filteredIncidents = incidents.filter((incident) => {
    const titleMatches = incident.title.toLowerCase().includes(searchText);

    const idMatches = String(incident.id).includes(searchText);

    return titleMatches || idMatches;
  });

  return (
    <>
      <h2>Incident dashboard</h2>

      <div className="dashboard-toolbar">
        <input
          type="search"
          placeholder="Search by title or ID..."
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          aria-label="Search incidents"
        />
      </div>

      {loading && <p>Loading incidents...</p>}

      {error && <p role="alert">{error}</p>}

      <IncidentBoard
        incidents={filteredIncidents}
        onOpenIncident={onOpenIncident}
      />
    </>
  );
}
