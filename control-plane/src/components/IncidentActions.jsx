export default function IncidentActions({
  incident,
  currentUser,
  actionLoading,
  actionError,
  responseLoading,
  onChangeStatus,
  onRespond,
}) {
  const canManageIncident =
    currentUser?.role === "SYSTEM_ADMIN" || currentUser?.role === "ADMIN";

  const isOwner = incident.owner?.id === currentUser?.id;

  const myResponse = incident.my_response;

  const isAcknowledged = myResponse === "ACKNOWLEDGED";
  const isUnavailable = myResponse === "UNAVAILABLE";

  const isResponder = incident.responders?.some(
    (responder) => responder.id === currentUser?.id,
  );

  const canResolve =
    canManageIncident && isOwner && incident.status === "IN_PROGRESS";

  const canAssign =
    canManageIncident && incident.status === "NEW" && !incident.owner;
  return (
    <>
      <h3>Actions</h3>

      {actionError && <p role="alert">{actionError}</p>}

      {canAssign && (
        <button
          type="button"
          className="assign-me-button"
          disabled={actionLoading}
          onClick={() => onChangeStatus("claim")}
        >
          {actionLoading ? "ASSIGNING..." : "ASSIGN TO ME"}
        </button>
      )}

      {incident.my_response && (
        <p>
          Your response: <strong>{incident.my_response}</strong>
        </p>
      )}

      <p>
        Status: <strong>{incident.status}</strong>
      </p>

      <p>
        Assigned to: <strong>{incident.owner?.username || "Unassigned"}</strong>
      </p>

      <select
        id="incident-status"
        value={incident.status}
        disabled={
          actionLoading ||
          incident.status === "RESOLVED" ||
          !canManageIncident ||
          (incident.status === "IN_PROGRESS" && !canResolve)
        }
        onChange={(event) => {
          const nextStatus = event.target.value;

          if (incident.status === "NEW" && nextStatus === "IN_PROGRESS") {
            onChangeStatus("claim");
          }

          if (canResolve && nextStatus === "RESOLVED") {
            onChangeStatus("resolve");
          }
        }}
      >
        <option value={incident.status}>{incident.status}</option>

        {canManageIncident && incident.status === "NEW" && (
          <option value="IN_PROGRESS">IN_PROGRESS</option>
        )}

        {canResolve && <option value="RESOLVED">RESOLVED</option>}
      </select>

      {incident.status === "NEW" && !incident.owner && (
        <div className="incident-actions">
          <button
            type="button"
            className={
              myResponse === "ACKNOWLEDGED"
                ? "response-button ack-active"
                : "response-button"
            }
            disabled={responseLoading || isAcknowledged}
            onClick={() => onRespond("acknowledge")}
          >
            ACKNOWLEDGE
          </button>

          <button
            type="button"
            className={
              myResponse === "UNAVAILABLE"
                ? "response-button unavailable-active"
                : "response-button"
            }
            disabled={responseLoading || isAcknowledged || isUnavailable}
            onClick={() => onRespond("unavailable")}
          >
            UNAVAILABLE
          </button>
        </div>
      )}
      {incident.status === "IN_PROGRESS" && canManageIncident && isOwner && (
        <button
          type="button"
          disabled={actionLoading || incident.help_requested}
          onClick={() => onChangeStatus("request-help")}
        >
          {incident.help_requested ? "HELP REQUESTED" : "REQUEST HELP"}
        </button>
      )}

      {incident.status === "IN_PROGRESS" &&
        canManageIncident &&
        !isOwner &&
        !isResponder && (
          <button
            type="button"
            disabled={actionLoading}
            onClick={() => onChangeStatus("join")}
          >
            JOIN INCIDENT
          </button>
        )}

      {incident.responders?.length > 0 && (
        <div>
          <h3>Responders</h3>

          {incident.responders.map((responder) => (
            <p key={responder.id}>{responder.username}</p>
          ))}
        </div>
      )}

      {incident.status === "RESOLVED" && <p>Incident resolved</p>}
    </>
  );
}
