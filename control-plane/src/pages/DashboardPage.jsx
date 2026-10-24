import IncidentBoard from "../components/IncidentBoard";

export default function DashboardPage({
  incidents,
  search,
  onSearchChange,
  loading,
  error,
  onOpenIncident,
}) {
  const query = search.trim().toLowerCase();

  const filtered = incidents.filter(
    (item) =>
      item.title?.toLowerCase().includes(query) ||
      String(item.id).includes(query),
  );

  return (
    <section className="dashboard-page final-dashboard">
      <div className="board-panel">
        <div className="board-toolbar">
          <h2>Incident board</h2>

          <input
            type="search"
            aria-label="Search incidents"
            placeholder="Search incidents..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </div>

        {loading && <p>Loading incidents...</p>}

        {error && <p role="alert">{error}</p>}

        <IncidentBoard incidents={filtered} onOpenIncident={onOpenIncident} />
      </div>
    </section>
  );
}
