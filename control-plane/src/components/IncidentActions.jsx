export default function IncidentActions({
  incident,
  currentUser,
  actionLoading,
  actionError,
  responseLoading,
  onChangeStatus,
  onRespond,
}) {
  const canManage =
    currentUser?.role === "SYSTEM_ADMIN" || currentUser?.role === "ADMIN";

  const isOwner = incident.owner?.id === currentUser?.id;

  const response = incident.my_response;

  const acknowledged = response === "ACKNOWLEDGED";

  const unavailable = response === "UNAVAILABLE";

  const isResponder = incident.responders?.some(
    (r) => r.id === currentUser?.id,
  );

  const canAssign = canManage && incident.status === "NEW" && !incident.owner;
  const canResolve = canManage && isOwner && incident.status === "IN_PROGRESS";
  const canRespond = incident.status === "NEW" && !incident.owner;

  return (
    <div className="final-incident-actions">
      <div className="final-incident-state">
        <div className="final-state-item">
          <span>Incident status</span>

          <strong
            className={`final-status status-${incident.status?.toLowerCase()}`}
          >
            {incident.status?.replaceAll("_", " ")}
          </strong>
        </div>
        <div className="final-state-item">
          <span>Assigned to</span>

          <strong>{incident.owner?.username || "Unassigned"}</strong>
        </div>
      </div>
      <div className="final-response-section">
        <div className="final-response-title">
          <div>
            <h3>Response actions</h3>

            <p>Choose your response to this incident</p>
          </div>

          {incident.status === "NEW" && !incident.owner && response && (
            <small>Your response: {response.replaceAll("_", " ")}</small>
          )}
        </div>

        {actionError && <p role="alert">{actionError}</p>}

        <div className="final-response-buttons">
          {canAssign && (
            <button
              type="button"
              className="final-action-btn final-assign"
              disabled={actionLoading}
              onClick={() => onChangeStatus("claim")}
            >
              {actionLoading ? "ASSIGNING..." : "ASSIGN TO ME"}
            </button>
          )}

          {canRespond && (
            <button
              type="button"
              className="final-action-btn final-ack"
              disabled={responseLoading || acknowledged}
              onClick={() => onRespond("acknowledge")}
            >
              {acknowledged ? "ACKNOWLEDGED" : "ACKNOWLEDGE"}
            </button>
          )}

          {canRespond && (
            <button
              type="button"
              className="final-action-btn final-unavailable"
              disabled={responseLoading || acknowledged || unavailable}
              onClick={() => onRespond("unavailable")}
            >
              {unavailable ? "MARKED UNAVAILABLE" : "MARK AS UNAVAILABLE"}
            </button>
          )}

          {canResolve && (
            <button
              type="button"
              className="final-action-btn final-resolve"
              disabled={actionLoading}
              onClick={() => onChangeStatus("resolve")}
            >
              {actionLoading ? "RESOLVING..." : "RESOLVE INCIDENT"}
            </button>
          )}

          {incident.status === "IN_PROGRESS" && canManage && isOwner && (
            <button
              type="button"
              className="final-action-btn final-help"
              disabled={actionLoading || incident.help_requested}
              onClick={() => onChangeStatus("request-help")}
            >
              {incident.help_requested ? "HELP REQUESTED" : "REQUEST HELP"}
            </button>
          )}

          {incident.status === "IN_PROGRESS" &&
            canManage &&
            !isOwner &&
            !isResponder && (
              <button
                type="button"
                className="final-action-btn final-join"
                disabled={actionLoading}
                onClick={() => onChangeStatus("join")}
              >
                JOIN INCIDENT
              </button>
            )}
        </div>

        {incident.status === "RESOLVED" && (
          <p className="final-muted">This incident is resolved.</p>
        )}
      </div>

      {incident.responders?.length > 0 && (
        <div className="final-responders">
          <h3>Responders</h3>

          <p>{incident.responders.map((r) => r.username).join(", ")}</p>
        </div>
      )}
    </div>
  );
}
