export default function Navigation({
  activePage,
  onDashboardClick,
  onCreateClick,
}) {
  return (
    <nav className="control-navigation">
      <button
        type="button"
        className={activePage === "dashboard" ? "nav-active" : ""}
        onClick={onDashboardClick}
      >
        Dashboard
      </button>

      <button
        type="button"
        className={activePage === "create" ? "nav-active" : ""}
        onClick={onCreateClick}
      >
        + Create Incident
      </button>
    </nav>
  );
}
