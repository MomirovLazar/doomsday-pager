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
    <form className="login-form" onSubmit={onSubmit}>
      <h2>Welcome back</h2>

      <p>Sign in to the incident control center</p>

      <label>
        Username
        <input
          autoComplete="username"
          required
          value={username}
          onChange={(e) => onUsernameChange(e.target.value)}
          placeholder="Username"
        />
      </label>

      <label>
        Password
        <input
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => onPasswordChange(e.target.value)}
          placeholder="Password"
        />
      </label>

      {error && <p role="alert">{error}</p>}

      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
