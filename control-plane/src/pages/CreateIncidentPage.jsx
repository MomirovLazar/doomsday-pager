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
    <section className="create-page">
      <div className="page-heading">
        <h1>Create Incident</h1>

        <p>Report a new incident to notify the response team</p>
      </div>

      <form className="create-panel" onSubmit={onSubmit}>
        <div className="create-grid">
          <label className="field wide">
            Incident title <em>*</em>
            <input
              required
              maxLength={200}
              value={incidentTitle}
              onChange={(e) => onIncidentTitleChange(e.target.value)}
              placeholder="Enter a short descriptive title"
            />
          </label>

          <label className="field">
            Priority <em>*</em>
            <select
              required
              value={incidentPriority}
              onChange={(e) => onIncidentPriorityChange(e.target.value)}
            >
              <option value="">Select priority</option>
              {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
          </label>

          <label className="field full">
            Description <em>*</em>
            <textarea
              required
              rows={7}
              value={incidentDescription}
              onChange={(e) => onIncidentDescriptionChange(e.target.value)}
              placeholder="Describe what happened, which services are affected, and any relevant details…"
            />
          </label>

          <label className="field full">
            Incident type <em>*</em>
            <select
              required
              value={incidentType}
              onChange={(e) => onIncidentTypeChange(e.target.value)}
            >
              <option value="">Select type</option>
              {[
                "NETWORK",
                "SERVER",
                "DATABASE",
                "SECURITY",
                "APPLICATION",
                "OTHER",
              ].map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="create-footer">
          {createError && <p role="alert">{createError}</p>}

          <button type="button" className="secondary-button" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="submit"
            className="primary-button"
            disabled={createLoading}
          >
            {createLoading ? "Creating…" : "＋ Create Incident"}
          </button>
        </div>
      </form>
    </section>
  );
}
