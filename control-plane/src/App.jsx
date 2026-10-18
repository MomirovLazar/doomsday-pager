import { useState } from "react";
import "./App.css";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);

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

      setCurrentUser(userData);
      setLoggedIn(true);
      setPassword("");

      console.log("Login successful");
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <main>
      <h1>Doomsday Pager</h1>
      <h2>Control Plane Login</h2>

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

      {error && <p role="alert">{error}</p>}

      {loggedIn && currentUser && (
        <div>
          <h2>Welcome, {currentUser.username}!</h2>
          <p>Role: {currentUser.role}</p>
          <p>Email: {currentUser.email}</p>
        </div>
      )}
    </main>
  );
}

export default App;
