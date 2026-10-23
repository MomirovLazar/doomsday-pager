import { useState } from "react";

import "./styles/global.css";
import "./styles/dashboard.css";
import "./styles/incidents.css";
import "./styles/forms.css";

import { login, getCurrentUser } from "./api/auth";
import {
  getIncidents,
  getIncident,
  createIncident,
  claimIncident,
  resolveIncident,
  acknowledgeIncident,
  markUnavailable,
  joinIncident,
  requestIncidentHelp,
  addIncidentComment,
} from "./api/incidents";

import LoginPage from "./pages/LoginPage";
import Navigation from "./components/Navigation";
import DashboardPage from "./pages/DashboardPage";
import IncidentDetailsPage from "./pages/IncidentDetailsPage";
import CreateIncidentPage from "./pages/CreateIncidentPage";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [token, setToken] = useState(null);

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

  async function handleLogin(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const data = await login(username, password);

      if (!data.access_token) {
        throw new Error("No access token recieved");
      }

      const userData = await getCurrentUser(data.access_token);

      setToken(data.access_token);
      setCurrentUser(userData);
      setLoggedIn(true);
      setPassword("");

      await loadIncidents(data.access_token);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadIncidents(access_token) {
    if (!access_token) {
      return;
    }

    setIncidentsLoading(true);
    setIncidentsError("");

    try {
      const data = await getIncidents(access_token);

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
      const createdIncident = await createIncident(token, {
        type: IncidentType,
        priority: incidentPriority,
        title: incidentTitle.trim(),
        description: incidentDescription.trim(),
      });

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
      const data = await getIncident(token, incidentId);

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

    const actions = {
      claim: claimIncident,
      resolve: resolveIncident,
      join: joinIncident,
      "request-help": requestIncidentHelp,
    };

    const excecuteAction = actions[action];

    if (!excecuteAction) {
      return;
    }

    setActionLoading(true);
    setActionError("");

    try {
      await excecuteAction(token, selectedIncident.id);
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

    const actions = {
      acknowledge: acknowledgeIncident,
      unavailable: markUnavailable,
    };

    const excecuteAction = actions[responseType];

    if (!excecuteAction) {
      return;
    }

    setResponseLoading(true);
    setActionError("");

    try {
      await excecuteAction(token, selectedIncident.id);
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
      await addIncidentComment(token, selectedIncident.id, content);

      setCommentText("");

      await openIncident(selectedIncidentId);
    } catch (error) {
      setCommentError(error.message);
    } finally {
      setCommentLoading(false);
    }
  }

  return (
    <main>
      <h1>Doomsday Pager</h1>

      {!loggedIn && (
        <LoginPage
          username={username}
          password={password}
          onUsernameChange={setUsername}
          onPasswordChange={setPassword}
          onSubmit={handleLogin}
          loading={loading}
          error={error}
        />
      )}

      {loggedIn && currentUser && (
        <div>
          <h2>Welcome, {currentUser.username}!</h2>
          <p>Role: {currentUser.role}</p>
          <p>Email: {currentUser.email}</p>
        </div>
      )}

      {loggedIn && (
        <section>
          <Navigation
            activePage={activePage}
            onDashboardClick={() => {
              setActivePage("dashboard");
              setSelectedIncidentId(null);
              setSelectedIncident(null);
              loadIncidents(token);
            }}
            onCreateClick={() => {
              setActivePage("create");
              setSelectedIncidentId(null);
              setSelectedIncident(null);
            }}
          />

          {activePage === "dashboard" && (
            <>
              {selectedIncidentId === null && (
                <DashboardPage
                  incidents={incidents}
                  search={search}
                  onSearchChange={setSearch}
                  loading={incidentsLoading}
                  error={incidentsError}
                  onOpenIncident={openIncident}
                />
              )}

              {selectedIncidentId !== null && (
                <IncidentDetailsPage
                  incident={selectedIncident}
                  currentUser={currentUser}
                  loading={incidentLoading}
                  error={incidentError}
                  onBack={() => {
                    setSelectedIncidentId(null);
                    setSelectedIncident(null);
                  }}
                  actionLoading={actionLoading}
                  actionError={actionError}
                  responseLoading={responseLoading}
                  onChangeStatus={changeIncidentStatus}
                  onRespond={respondToIncident}
                  commentText={commentText}
                  onCommentChange={setCommentText}
                  onSubmitComment={submitComment}
                  commentLoading={commentLoading}
                  commentError={commentError}
                  showHistory={showHistory}
                  onToggleHistory={() => setShowHistory(!showHistory)}
                />
              )}
            </>
          )}

          {activePage === "create" && (
            <CreateIncidentPage
              incidentType={IncidentType}
              onIncidentTypeChange={setIncidentType}
              incidentPriority={incidentPriority}
              onIncidentPriorityChange={setIncidentPriority}
              incidentTitle={incidentTitle}
              onIncidentTitleChange={setIncidentTitle}
              incidentDescription={incidentDescription}
              onIncidentDescriptionChange={setIncidentDescription}
              createLoading={createLoading}
              createError={createError}
              onSubmit={handleCreateIncident}
              onCancel={() => setActivePage("dashboard")}
            />
          )}
        </section>
      )}
    </main>
  );
}

export default App;
