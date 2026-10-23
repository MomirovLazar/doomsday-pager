export default function IncidentHistory({
  history,
  showHistory,
  onToggleHistory,
}) {
  return (
    <section className="incident-history">
      <button type="button" onClick={onToggleHistory}>
        {showHistory ? "▲ Hide Incident History" : "▼ Incident History"}
      </button>

      {showHistory && (
        <div className="history-list">
          <h3>Incident History</h3>

          {history?.length > 0 ? (
            history.map((event) => (
              <div className="history-item" key={event.id}>
                <strong>{event.action}</strong>

                <p>By: {event.performed_by}</p>

                {event.details && <p>{event.details}</p>}

                <small>{new Date(event.created_at).toLocaleString()}</small>
              </div>
            ))
          ) : (
            <p>No history available.</p>
          )}
        </div>
      )}
    </section>
  );
}
