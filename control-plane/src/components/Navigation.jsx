export default function Navigation({
  activePage,
  onDashboardClick,
  onCreateClick,
}) {
  return (
    <nav className="control-navigation">
      <button
        className={activePage === "dashboard" ? "nav-active" : ""}
        onClick={onDashboardClick}
      >
        ⌂ &nbsp; Dashboard
      </button>

      <button
        className={activePage === "create" ? "nav-active" : ""}
        onClick={onCreateClick}
      >
        ⊞ &nbsp; Create Incident
      </button>
    </nav>
  );
}
