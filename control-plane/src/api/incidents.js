import { apiRequest } from "./client";

export function getIncidents(token) {
    return apiRequest("/incidents", { token });
}

export function getIncident(token, incidentId) {
    return apiRequest(`/incidents/${incidentId}`, { token });
}

export function createIncident(token, incidentData) {
    return apiRequest("/incidents", {
        method: "POST",
        token,
        body: JSON.stringify(incidentData),
    });
}

function incidentAction(token, incidentId, action) {
    return apiRequest(`/incidents/${incidentId}/${action}`, {
        method: "POST",
        token,
    });
}

export function claimIncident(token, incidentId) {
    return incidentAction(token, incidentId, "claim");
}

export function resolveIncident(token, incidentId) {
    return incidentAction(token, incidentId, "resolve");
}

export function acknowledgeIncident(token, incidentId) {
    return incidentAction(token, incidentId, "acknowledge");
}

export function markUnavailable(token, incidentId) {
    return incidentAction(token, incidentId, "unavailable");
}

export function joinIncident(token, incidentId) {
    return incidentAction(token, incidentId, "join");
}

export function requestIncidentHelp(token, incidentId) {
    return incidentAction(token, incidentId, "request-help");
}

export function addIncidentComment(token, incidentId, content) {
    return apiRequest(`/incidents/${incidentId}/comments`, {
        method: "POST",
        token,
        body: JSON.stringify({ content })
    });
}