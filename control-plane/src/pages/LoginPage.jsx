export default function LoginPage({
  username,
  password,
  onUsernameChange,
  onPasswordChange,
  onSubmit,
  loading,
  error,
}) {
  return (
    <>
      <h2>Control Plane Login</h2>

      <form onSubmit={onSubmit}>
        <div>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(event) => onUsernameChange(event.target.value)}
            required
          />
        </div>

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => onPasswordChange(event.target.value)}
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      {error && <p role="alert">{error}</p>}
    </>
  );
}
