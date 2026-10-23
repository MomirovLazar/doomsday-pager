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
    <section className="incident-details">
      <button type="button" onClick={onBack}>
        ← Back to Dashboard
      </button>

      {loading && <p>Loading incident...</p>}

      {error && <p role="alert">{error}</p>}

      {incident && (
        <div className="incident-detail-content">
          <div className="incident-detail-header">
            <h2>{incident.title}</h2>

            <span>Incident #{incident.id}</span>
          </div>

          <div className="incident-detail-layout">
            <div className="incident-detail-main">
              <aside className="incident-detail-sidebar">
                <h3>Incident details</h3>

                <p>Priority: {incident.priority}</p>
                <p>Status: {incident.status}</p>

                <h3>Description</h3>

                <p>{incident.description || "No description provided"}</p>

                <IncidentActions
                  incident={incident}
                  currentUser={currentUser}
                  actionLoading={actionLoading}
                  actionError={actionError}
                  responseLoading={responseLoading}
                  onChangeStatus={onChangeStatus}
                  onRespond={onRespond}
                />
              </aside>
            </div>

            <IncidentComments variant="list" comments={incident.comments} />
          </div>

          {currentUser?.role === "ADMIN" && (
            <IncidentHistory
              history={incident.history}
              showHistory={showHistory}
              onToggleHistory={onToggleHistory}
            />
          )}

          <IncidentComments
            variant="form"
            commentText={commentText}
            onCommentChange={onCommentChange}
            onSubmitComment={onSubmitComment}
            commentLoading={commentLoading}
            commentError={commentError}
          />
        </div>
      )}
    </section>
  );
}
