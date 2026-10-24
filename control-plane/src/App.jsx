import { useEffect, useState } from "react";
import "./styles/global.css";
import "./styles/dashboard.css";
import "./styles/incidents.css";
import "./styles/forms.css";
import "./styles/operations.css";
import "./styles/final-touches.css";
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

export default function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState(() =>
    sessionStorage.getItem("pager_token"),
  );

  const [currentUser, setCurrentUser] = useState(null);
  const [restoring, setRestoring] = useState(
    Boolean(sessionStorage.getItem("pager_token")),
  );

  const [incidents, setIncidents] = useState([]);
  const [incidentsLoading, setIncidentsLoading] = useState(false);
  const [incidentsError, setIncidentsError] = useState("");
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [incidentLoading, setIncidentLoading] = useState(false);
  const [incidentError, setIncidentError] = useState("");
  const [incidentType, setIncidentType] = useState("");
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

  async function loadIncidents(auth, quiet = false) {
    if (!auth) return;
    if (!quiet) setIncidentsLoading(true);

    try {
      const data = await getIncidents(auth);

      setIncidents(Array.isArray(data) ? data : []);
      setIncidentsError("");
    } catch (e) {
      if (!quiet) setIncidentsError(e.message);
    } finally {
      if (!quiet) setIncidentsLoading(false);
    }
  }
  useEffect(() => {
    if (!token) {
      setRestoring(false);

      return;
    }

    let active = true;

    getCurrentUser(token)
      .then((user) => {
        if (!active) return;

        setCurrentUser(user);
        loadIncidents(token);
      })
      .catch(() => {
        if (!active) return;

        sessionStorage.removeItem("pager_token");

        setToken(null);
        setCurrentUser(null);
      })
      .finally(() => {
        if (active) setRestoring(false);
      });

    return () => {
      active = false;
    };
  }, [token]);

  useEffect(() => {
    if (!token || !currentUser) return;

    const id = setInterval(() => loadIncidents(token, true), 12000);

    return () => clearInterval(id);
  }, [token, currentUser]);

  function logout() {
    sessionStorage.removeItem("pager_token");

    setToken(null);
    setCurrentUser(null);
    setIncidents([]);
    setSelectedIncidentId(null);
    setSelectedIncident(null);
    setActivePage("dashboard");
  }

  async function handleLogin(e) {
    e.preventDefault();

    setLoading(true);
    setError("");

    try {
      const data = await login(username, password);

      if (!data.access_token) throw new Error("No access token received");

      const user = await getCurrentUser(data.access_token);
      sessionStorage.setItem("pager_token", data.access_token);

      setCurrentUser(user);
      setToken(data.access_token);
      setPassword("");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function openIncident(id) {
    setSelectedIncidentId(id);
    setSelectedIncident(null);
    setShowHistory(false);
    setIncidentLoading(true);
    setIncidentError("");
    setActivePage("dashboard");

    try {
      setSelectedIncident(await getIncident(token, id));
    } catch (e) {
      setIncidentError(e.message);
    } finally {
      setIncidentLoading(false);
    }
  }

  async function handleCreateIncident(e) {
    e.preventDefault();

    if (createLoading || !token) return;

    setCreateLoading(true);
    setCreateError("");

    try {
      const created = await createIncident(token, {
        type: incidentType,
        priority: incidentPriority,
        title: incidentTitle.trim(),
        description: incidentDescription.trim(),
      });

      setIncidentType("");
      setIncidentPriority("");
      setIncidentTitle("");
      setIncidentDescription("");
      setSearch("");

      await loadIncidents(token);
      await openIncident(created.id);
    } catch (e) {
      setCreateError(e.message);
    } finally {
      setCreateLoading(false);
    }
  }

  async function changeIncidentStatus(action) {
    if (!selectedIncident || !token || actionLoading) return;

    const actions = {
      claim: claimIncident,
      resolve: resolveIncident,
      join: joinIncident,
      "request-help": requestIncidentHelp,
    };

    if (!actions[action]) return;

    setActionLoading(true);
    setActionError("");

    try {
      await actions[action](token, selectedIncident.id);
      const [detail] = await Promise.all([
        getIncident(token, selectedIncident.id),
        loadIncidents(token, true),
      ]);

      setSelectedIncident(detail);
    } catch (e) {
      setActionError(e.message);
    } finally {
      setActionLoading(false);
    }
  }

  async function respondToIncident(action) {
    if (!selectedIncident || !token || responseLoading) return;

    const actions = {
      acknowledge: acknowledgeIncident,
      unavailable: markUnavailable,
    };

    if (!actions[action]) return;

    setResponseLoading(true);
    setActionError("");

    try {
      await actions[action](token, selectedIncident.id);
      setSelectedIncident(await getIncident(token, selectedIncident.id));
    } catch (e) {
      setActionError(e.message);
    } finally {
      setResponseLoading(false);
    }
  }

  async function submitComment(e) {
    e.preventDefault();

    if (!commentText.trim() || !selectedIncident || !token || commentLoading)
      return;

    setCommentLoading(true);
    setCommentError("");

    try {
      await addIncidentComment(token, selectedIncident.id, commentText.trim());

      setCommentText("");
      setSelectedIncident(await getIncident(token, selectedIncident.id));
    } catch (e) {
      setCommentError(e.message);
    } finally {
      setCommentLoading(false);
    }
  }

  if (restoring)
    return (
      <div className="boot-screen">
        DOOMSDAY PAGER <span>Restoring session…</span>
      </div>
    );

  if (!token || !currentUser)
    return (
      <div className="auth-screen">
        <div className="auth-brand">
          <div className="brand-icon">♧</div>
          <h1>DOOMSDAY PAGER</h1>

          <p>INCIDENT CONTROL CENTER</p>
        </div>
        <div className="auth-card">
          <LoginPage
            username={username}
            password={password}
            onUsernameChange={setUsername}
            onPasswordChange={setPassword}
            onSubmit={handleLogin}
            loading={loading}
            error={error}
          />
        </div>
      </div>
    );

  return (
    <div className="ops-shell">
      <aside className="ops-sidebar">
        <div className="brand">
          <div className="brand-icon">♧</div>
          <div>
            <strong>DOOMSDAY PAGER</strong>
            <small>INCIDENT CONTROL CENTER</small>
          </div>
        </div>

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
        <div className="sidebar-bottom">
          <button onClick={logout} className="logout-button">
            ↪ &nbsp; Log out
          </button>
        </div>
      </aside>
      <main className="ops-main">
        <header className="ops-topbar">
          <span className="online-indicator">
            <i /> System online
          </span>
          <div className="user-chip">
            <span className="user-avatar">
              {currentUser.username?.slice(0, 2).toUpperCase()}
            </span>
            <div>
              <strong>{currentUser.username}</strong>
              <small>{currentUser.role?.replaceAll("_", " ")}</small>
            </div>
          </div>
        </header>

        {activePage === "dashboard" && selectedIncidentId === null && (
          <DashboardPage
            incidents={incidents}
            search={search}
            onSearchChange={setSearch}
            loading={incidentsLoading}
            error={incidentsError}
            onOpenIncident={openIncident}
          />
        )}

        {activePage === "dashboard" && selectedIncidentId !== null && (
          <IncidentDetailsPage
            incident={selectedIncident}
            currentUser={currentUser}
            loading={incidentLoading}
            error={incidentError}
            onBack={() => {
              setSelectedIncidentId(null);
              setSelectedIncident(null);
              loadIncidents(token);
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

        {activePage === "create" && (
          <CreateIncidentPage
            incidentType={incidentType}
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
      </main>
    </div>
  );
}
