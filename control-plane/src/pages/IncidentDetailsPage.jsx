import IncidentActions from "../components/IncidentActions";
import IncidentComments from "../components/IncidentComments";
import IncidentHistory from "../components/IncidentHistory";
export default function IncidentDetailsPage({
  incident,
  currentUser,
  loading,
  error,
  onBack,
  actionLoading,
  actionError,
  responseLoading,
  onChangeStatus,
  onRespond,
  commentText,
  onCommentChange,
  onSubmitComment,
  commentLoading,
  commentError,
  showHistory,
  onToggleHistory,
}) {
  return (
    <section className="detail-page">
      <button className="back-link" onClick={onBack}>
        ← Back to dashboard
      </button>

      {loading && <p>Loading incident…</p>}

      {error && <p role="alert">{error}</p>}

      {incident && (
        <>
          <div className="detail-title">
            <div>
              <div className="detail-title-line">
                <span>#{incident.id}</span>

                <h1>{incident.title}</h1>

                <span
                  className={`priority-pill ${incident.priority?.toLowerCase()}`}
                >
                  {incident.priority}
                </span>
              </div>
              <div className="detail-subline">
                <span>● {incident.status?.replaceAll("_", " ")}</span>
                <span>
                  ◷{" "}
                  {incident.created_at
                    ? new Date(incident.created_at).toLocaleString()
                    : ""}
                </span>
                <span>♙ Owner: {incident.owner?.username || "Unassigned"}</span>
                <span>Type: {incident.type}</span>
              </div>
            </div>
          </div>

          <div className="detail-grid">
            <div className="detail-left">
              <div className="detail-panel">
                <h3>Description</h3>

                <p className="description-text">
                  {incident.description || "No description provided"}
                </p>

                <hr />

                <IncidentActions
                  incident={incident}
                  currentUser={currentUser}
                  actionLoading={actionLoading}
                  actionError={actionError}
                  responseLoading={responseLoading}
                  onChangeStatus={onChangeStatus}
                  onRespond={onRespond}
                />
              </div>

              <div className="detail-panel">
                <h3>Incident information</h3>

                <div className="info-grid">
                  <div>
                    <small>Created by</small>
                    <strong>{incident.created_by?.username || "—"}</strong>
                  </div>

                  <div>
                    <small>Owner</small>
                    <strong>{incident.owner?.username || "Unassigned"}</strong>
                  </div>

                  <div>
                    <small>Priority</small>
                    <strong>{incident.priority}</strong>
                  </div>

                  <div>
                    <small>Type</small>
                    <strong>{incident.type}</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="detail-right">
              <div className="detail-panel">
                <IncidentComments variant="list" comments={incident.comments} />
                <IncidentComments
                  variant="form"
                  commentText={commentText}
                  onCommentChange={onCommentChange}
                  onSubmitComment={onSubmitComment}
                  commentLoading={commentLoading}
                  commentError={commentError}
                />
              </div>

              {currentUser?.role === "ADMIN" && (
                <div className="detail-panel">
                  <IncidentHistory
                    history={incident.history}
                    showHistory={showHistory}
                    onToggleHistory={onToggleHistory}
                  />
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
