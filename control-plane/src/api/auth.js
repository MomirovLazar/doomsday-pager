import { apiRequest } from "./client";

export function login(username, password) {
  return apiRequest("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function getCurrentUser(token) {
  return apiRequest("/me", { token });
}
