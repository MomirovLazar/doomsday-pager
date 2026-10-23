export default function CreateIncidentPage({
  incidentType,
  onIncidentTypeChange,
  incidentPriority,
  onIncidentPriorityChange,
  incidentTitle,
  onIncidentTitleChange,
  incidentDescription,
  onIncidentDescriptionChange,
  createLoading,
  createError,
  onSubmit,
  onCancel,
}) {
  return (
    <div className="create-incident-page">
      <h2>Create Incident</h2>
      <p>Create a new incident for the response team</p>

      <form className="create-incident-form" onSubmit={onSubmit}>
        <div className="create-form-row">
          <div className="create-form-field">
            <label htmlFor="incident-type">Incident Type</label>

            <select
              id="incident-type"
              value={incidentType}
              onChange={(event) => onIncidentTypeChange(event.target.value)}
              required
            >
              <option value="">Select type</option>
              <option value="NETWORK">Network</option>
              <option value="SERVER">Server</option>
              <option value="DATABASE">Database</option>
              <option value="SECURITY">Security</option>
              <option value="APPLICATION">Application</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div className="create-form-field">
            <label htmlFor="incident-priority">Priority</label>

            <select
              id="incident-priority"
              value={incidentPriority}
              onChange={(event) => onIncidentPriorityChange(event.target.value)}
              required
            >
              <option value="">Select priority</option>
              <option value="LOW">LOW</option>
              <option value="MEDIUM">MEDIUM</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>

          <div className="create-form-field">
            <label htmlFor="incident-title">Incident title</label>

            <input
              id="incident-title"
              type="text"
              value={incidentTitle}
              onChange={(event) => onIncidentTitleChange(event.target.value)}
              placeholder="Briefly describe the problem..."
              maxLength={200}
              required
            />
          </div>

          <div className="create-form-field">
            <label htmlFor="incident-description">Description</label>

            <textarea
              id="incident-description"
              value={incidentDescription}
              onChange={(event) =>
                onIncidentDescriptionChange(event.target.value)
              }
              placeholder="What happened? Describe the problem."
              rows={6}
              required
            />
          </div>

          <div className="create-form-actions">
            {createError && <p role="alert">{createError}</p>}

            <button type="button" onClick={onCancel}>
              Cancel
            </button>

            <button
              type="submit"
              className="create-submit-button"
              disabled={createLoading}
            >
              {createLoading ? "Creating..." : "Create Incident"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
