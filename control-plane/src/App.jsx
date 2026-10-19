import { useState } from "react";
import "./App.css";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);

  async function handleLogin(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          password: password,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Invalid username or password");
        }

        throw new Error("Login failed. Please try again.");
      }

      const data = await response.json();

      if (!data.access_token) {
        throw new Error("No access token received");
      }

      const userResponse = await fetch("http://127.0.0.1:8000/me", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      });

      if (!userResponse.ok) {
        throw new Error("Failed to load user profile");
      }

      const userData = await userResponse.json();

      setToken(data.access_token);
      setCurrentUser(userData);
      setLoggedIn(true);
      setPassword("");

      await loadIncidents(data.access_token);

      console.log("Login successful");
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  const [incidents, setIncidents] = useState([]);
  const [incidentsLoading, setIncidentsLoading] = useState(false);
  const [incidentsError, setIncidentsError] = useState("");
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [incidentLoading, setIncidentLoading] = useState(false);
  const [incidentError, setIncidentError] = useState("");
  const [IncidentType, setIncidentType] = useState("");
  const [incidentPriority, setIncidentPriority] = useState("");
  const [incidentTitle, setIncidentTitle] = useState("");
  const [incidentDescription, setIncidentDescription] = useState("");

  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");

  const [search, setSearch] = useState("");

  const [activePage, setActivePage] = useState("dashboard");

  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState("");

  const [responseLoading, setResponseLoading] = useState(false);

  const [commentText, setCommentText] = useState("");
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentError, setCommentError] = useState("");

  const [showHistory, setShowHistory] = useState(false);

  async function loadIncidents(access_token) {
    if (!access_token) {
      return;
    }

    setIncidentsLoading(true);
    setIncidentsError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/incidents", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${access_token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load incidents");
      }

      const data = await response.json();
      setIncidents(data);
    } catch (error) {
      setIncidentsError(error.message);
    } finally {
      setIncidentsLoading(false);
    }
  }

  async function handleCreateIncident(event) {
    event.preventDefault();

    if (createLoading || !token) return;

    setCreateLoading(true);
    setCreateError("");

    try {
      const response = await fetch("http://127.0.0.1:8000/incidents", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          type: IncidentType,
          priority: incidentPriority,
          title: incidentTitle.trim(),
          description: incidentDescription.trim(),
        }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(
          `HTTP ${response.status}: ${JSON.stringify(data?.detail ?? "Failed to create incident")}`,
        );
      }

      const createdIncident = await response.json();

      setIncidentType("");
      setIncidentPriority("");
      setIncidentTitle("");
      setIncidentDescription("");

      setSearch("");
      setActivePage("dashboard");

      await loadIncidents(token);
      await openIncident(createdIncident.id);
    } catch (error) {
      setCreateError(error.message);
    } finally {
      setCreateLoading(false);
    }
  }

  async function openIncident(incidentId) {
    setSelectedIncidentId(incidentId);
    setShowHistory(false);
    setSelectedIncident(null);
    setIncidentLoading(true);
    setIncidentError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/incidents/${incidentId}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error("Failed to load incident details");
      }

      const data = await response.json();
      setSelectedIncident(data);
    } catch (error) {
      setIncidentError(error.message);
    } finally {
      setIncidentLoading(false);
    }
  }

  async function changeIncidentStatus(action) {
    if (!selectedIncident || !token || actionLoading) {
      return;
    }

    setActionLoading(true);
    setActionError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/incidents/${selectedIncident.id}/${action}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to ${action} incident`);
      }

      await openIncident(selectedIncident.id);
      await loadIncidents(token);
    } catch (error) {
      setActionError(error.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function respondToIncident(responseType) {
    if (!selectedIncident || !token || responseLoading) {
      return;
    }

    setResponseLoading(true);
    setActionError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/incidents/${selectedIncident.id}/${responseType}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);

        throw new Error(
          `HTTP ${response.status}: ${
            typeof errorData?.detail === "string"
              ? errorData.detail
              : JSON.stringify(errorData?.detail ?? "Unknown error")
          }`,
        );
      }

      await openIncident(selectedIncident.id);
    } catch (error) {
      setActionError(error.message);
    } finally {
      setResponseLoading(false);
    }
  }

  async function submitComment(event) {
    event.preventDefault();

    const content = commentText.trim();

    if (!content || !selectedIncident || !token || commentLoading) {
      return;
    }

    setCommentLoading(true);
    setCommentError("");

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/incidents/${selectedIncident.id}/comments`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ content }),
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);

        throw new Error(
          `HTTP ${response.status}: ${
            typeof errorData?.detail === "string"
              ? errorData.detail
              : JSON.stringify(errorData?.detail ?? "Unknown error")
          }`,
        );
      }

      setCommentText("");
      await openIncident(selectedIncidentId);
    } catch (error) {
      setCommentError(error.message);
    } finally {
      setCommentLoading(false);
    }
  }

  const filteredIncidents = incidents.filter((incident) => {
    const searchText = search.toLowerCase().trim();

    const titleMatches = incident.title.toLowerCase().includes(searchText);

    const idMatches = String(incident.id).includes(searchText);

    return titleMatches || idMatches;
  });

  const newIncidents = filteredIncidents.filter(
    (incident) => incident.status === "NEW",
  );

  const inProgressIncidents = filteredIncidents.filter(
    (incident) => incident.status === "IN_PROGRESS",
  );

  const resolvedIncidents = filteredIncidents.filter(
    (incident) => incident.status === "RESOLVED",
  );

  return (
    <main>
      <h1>Doomsday Pager</h1>
      {!loggedIn && <h2>Control Plane Login</h2>}

      {!loggedIn && (
        <form onSubmit={handleLogin}>
          <div>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </div>

          <div>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      )}

      {!loggedIn && error && <p role="alert">{error}</p>}

      {loggedIn && currentUser && (
        <div>
          <h2>Welcome, {currentUser.username}!</h2>
          <p>Role: {currentUser.role}</p>
          <p>Email: {currentUser.email}</p>
        </div>
      )}

      {loggedIn && (
        <section>
          <nav className="control-navigation">
            <button
              type="button"
              className={activePage === "dashboard" ? "nav-active" : ""}
              onClick={() => {
                setActivePage("dashboard");
                setSelectedIncidentId(null);
                setSelectedIncident(null);
                loadIncidents(token);
              }}
            >
              Dashboard
            </button>

            <button
              type="button"
              className={activePage === "create" ? "nav-active" : ""}
              onClick={() => {
                setActivePage("create");
                setSelectedIncidentId(null);
                setSelectedIncident(null);
              }}
            >
              + Create Incident
            </button>
          </nav>

          {activePage === "dashboard" && (
            <>
              <h2>Incident dashboard</h2>

              <div className="dashboard-toolbar">
                <input
                  type="search"
                  placeholder="Search by title or ID..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  aria-label="Search incidents"
                />
              </div>

              {incidentsLoading && <p>Loading incidents...</p>}

              {incidentsError && <p role="alert">{incidentsError}</p>}

              {selectedIncidentId !== null && (
                <section className="incident-details">
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedIncidentId(null);
                      setSelectedIncident(null);
                    }}
                  >
                    ← Back to Dashboard
                  </button>

                  {incidentLoading && <p>Loading incident...</p>}

                  {incidentError && <p role="alert">{incidentError}</p>}

                  {selectedIncident && (
                    <div className="incident-detail-content">
                      <div className="incident-detail-header">
                        <h2>{selectedIncident.title}</h2>
                        <span>Incident #{selectedIncident.id}</span>
                      </div>

                      <div className="incident-detail-layout">
                        <div className="incident-detail-main">
                          <aside className="incident-detail-sidebar">
                            <h3>Incident details</h3>

                            <p>Priority: {selectedIncident.priority}</p>
                            <p>Status: {selectedIncident.status}</p>

                            <h3>Description</h3>
                            <p>
                              {selectedIncident.description ||
                                "No description provided."}
                            </p>

                            <h3>Actions</h3>

                            {actionError && <p role="alert">{actionError}</p>}

                            {selectedIncident.my_response && (
                              <p>
                                Your response:{" "}
                                <strong>{selectedIncident.my_response}</strong>
                              </p>
                            )}

                            <label htmlFor="incident-status">Status</label>

                            <select
                              id="incident-status"
                              value={selectedIncident.status}
                              disabled={
                                actionLoading ||
                                selectedIncident.status === "RESOLVED"
                              }
                              onChange={(event) => {
                                const nextStatus = event.target.value;

                                if (
                                  selectedIncident.status === "NEW" &&
                                  nextStatus === "IN_PROGRESS"
                                ) {
                                  changeIncidentStatus("claim");
                                }

                                if (
                                  selectedIncident.status === "IN_PROGRESS" &&
                                  nextStatus === "RESOLVED"
                                ) {
                                  changeIncidentStatus("resolve");
                                }
                              }}
                            >
                              <option value={selectedIncident.status}>
                                {selectedIncident.status}
                              </option>

                              {selectedIncident.status === "NEW" && (
                                <option value="IN_PROGRESS">IN_PROGRESS</option>
                              )}

                              {selectedIncident.status === "IN_PROGRESS" && (
                                <option value="RESOLVED">RESOLVED</option>
                              )}
                            </select>

                            {selectedIncident.status === "NEW" && (
                              <div className="incident-actions">
                                <button
                                  type="button"
                                  disabled={responseLoading}
                                  onClick={() =>
                                    respondToIncident("acknowledge")
                                  }
                                >
                                  ACKNOWLEDGE
                                </button>

                                <button
                                  type="button"
                                  disabled={responseLoading}
                                  onClick={() =>
                                    respondToIncident("unavailable")
                                  }
                                >
                                  UNAVAILABLE
                                </button>
                              </div>
                            )}

                            {selectedIncident.owner && (
                              <p>
                                Working on: {selectedIncident.owner.username}
                              </p>
                            )}

                            {selectedIncident.status === "IN_PROGRESS" &&
                              selectedIncident.owner?.id ===
                                currentUser?.id && (
                                <button
                                  type="button"
                                  disabled={
                                    actionLoading ||
                                    selectedIncident.help_requested
                                  }
                                  onClick={() =>
                                    changeIncidentStatus("request-help")
                                  }
                                >
                                  {selectedIncident.help_requested
                                    ? "HELP REQUESTED"
                                    : "REQUEST HELP"}
                                </button>
                              )}

                            {selectedIncident.status === "IN_PROGRESS" &&
                              currentUser?.role !== "L2" &&
                              selectedIncident.owner?.id !== currentUser?.id &&
                              !selectedIncident.responders?.some(
                                (responder) => responder.id === currentUser?.id,
                              ) && (
                                <button
                                  type="button"
                                  disabled={actionLoading}
                                  onClick={() => changeIncidentStatus("join")}
                                >
                                  JOIN INCIDENT
                                </button>
                              )}

                            {selectedIncident.responders?.length > 0 && (
                              <div>
                                <h3>Responders</h3>

                                {selectedIncident.responders.map(
                                  (responder) => (
                                    <p key={responder.id}>
                                      {responder.username}
                                    </p>
                                  ),
                                )}
                              </div>
                            )}

                            {selectedIncident.status === "RESOLVED" && (
                              <p>Incident resolved</p>
                            )}
                          </aside>
                        </div>

                        <div className="incident-comments">
                          <h3>
                            Comments ({selectedIncident.comments?.length ?? 0})
                          </h3>

                          {Array.isArray(selectedIncident.comments) &&
                          selectedIncident.comments.length > 0 ? (
                            <div className="comments-list">
                              {selectedIncident.comments.map((comment) => (
                                <div className="comment-item" key={comment.id}>
                                  <strong>{comment.author}</strong>

                                  <p>{comment.content}</p>

                                  <small>
                                    {new Date(
                                      comment.created_at,
                                    ).toLocaleString()}
                                  </small>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p>No comments yet.</p>
                          )}
                        </div>
                      </div>

                      {currentUser?.role === "ADMIN" && (
                        <section className="incident-history">
                          <button
                            type="button"
                            onClick={() => setShowHistory(!showHistory)}
                          >
                            {showHistory
                              ? "▲ Hide Incident History"
                              : "▼ Incident History"}
                          </button>

                          {showHistory && (
                            <div className="history-list">
                              <h3>Incident History</h3>

                              {selectedIncident.history?.length > 0 ? (
                                selectedIncident.history.map((event) => (
                                  <div className="history-item" key={event.id}>
                                    <strong>{event.action}</strong>
                                    <p>By: {event.performed_by}</p>

                                    {event.details && <p>{event.details}</p>}

                                    <small>
                                      {new Date(
                                        event.created_at,
                                      ).toLocaleString()}
                                    </small>
                                  </div>
                                ))
                              ) : (
                                <p>No history available.</p>
                              )}
                            </div>
                          )}
                        </section>
                      )}

                      <form onSubmit={submitComment} className="comment-form">
                        <textarea
                          value={commentText}
                          onChange={(event) =>
                            setCommentText(event.target.value)
                          }
                          placeholder="Write a comment..."
                          rows={3}
                          maxLength={2000}
                          required
                        ></textarea>

                        {commentError && <p role="alert">{commentError}</p>}

                        <button
                          type="submit"
                          disabled={commentLoading || !commentText.trim()}
                        >
                          {commentLoading ? "Sending..." : "Send comment"}
                        </button>
                      </form>
                    </div>
                  )}
                </section>
              )}

              {selectedIncidentId === null && (
                <div className="incident-board">
                  {[
                    { title: "NEW", items: newIncidents },
                    { title: "IN PROGRESS", items: inProgressIncidents },
                    { title: "RESOLVED", items: resolvedIncidents },
                  ].map((column) => (
                    <div className="incident-column" key={column.title}>
                      <h3>
                        {column.title} ({column.items.length})
                      </h3>

                      <div className="incident-list">
                        {column.items.map((incident) => (
                          <button
                            key={incident.id}
                            type="button"
                            className="incident-card"
                            onClick={() => openIncident(incident.id)}
                          >
                            <strong>{incident.title}</strong>
                            <span>#{incident.id}</span>
                            <span>Priority: {incident.priority}</span>
                          </button>
                        ))}

                        {column.items.length === 0 && (
                          <p className="empty-column">No incidents</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
          {activePage === "create" && (
            <div className="create-incident-page">
              <h2>Create Incident</h2>
              <p>Create a new incident for the response team</p>

              <form
                className="create-incident-form"
                onSubmit={handleCreateIncident}
              >
                <div className="create-form-row">
                  <div className="create-form-field">
                    <label htmlFor="incident-type">Incident Type</label>

                    <select
                      id="incident-type"
                      value={IncidentType}
                      onChange={(event) => setIncidentType(event.target.value)}
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
                      onChange={(event) =>
                        setIncidentPriority(event.target.value)
                      }
                      required
                    >
                      <option value="">Select priority</option>
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                      <option value="CRITICAL">CRITCAl</option>
                    </select>
                  </div>

                  <div className="create-form-field">
                    <label htmlFor="incident-title">Incident title</label>

                    <input
                      id="incident-title"
                      type="text"
                      value={incidentTitle}
                      onChange={(event) => setIncidentTitle(event.target.value)}
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
                        setIncidentDescription(event.target.value)
                      }
                      placeholder="What happend? Describe the problem."
                      rows={6}
                      required
                    ></textarea>
                  </div>

                  <div className="create-form-actions">
                    {createError && <p role="alert">{createError}</p>}

                    <button
                      type="button"
                      onClick={() => setActivePage("dashboard")}
                    >
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
          )}
        </section>
      )}
    </main>
  );
}

export default App;
