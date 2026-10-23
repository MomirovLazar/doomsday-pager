package com.doomsdaypager.app.data.repository

import com.doomsdaypager.app.data.model.Incident
import com.doomsdaypager.app.data.remote.ApiClient

class IncidentRepository {

    fun getIncidents(token: String): List<Incident> {
        val response = ApiClient.getIncidents(token)

        return List(response.length()) { index ->
            val json = response.getJSONObject(index)

            Incident(
                id = json.getInt("id"),
                title = json.optString("title", "Untitled incident"),
                description = json.optString("description", ""),
                status = json.optString("status", ""),
                priority = json.optString("priority", "")
            )
        }
    }

    fun getIncidentDetails(token: String, incidentId: Int): Incident {
        val json = ApiClient.getIncidentDetails(token, incidentId)

        val respondersJson = json.optJSONArray("responders")
        val commentsJson = json.optJSONArray("comments")
        val historyJson = json.optJSONArray("history")

        return Incident(
            id = json.getInt("id"),
            title = json.optString("title"),
            description = json.optString("description"),
            status = json.optString("status"),
            priority = json.optString("priority"),
            type = json.optString("type"),
            createdBy = json.optJSONObject("created_by")?.optString("username").orEmpty(),
            owner = json.optJSONObject("owner")?.optString("username").orEmpty(),

            responders = List(respondersJson?.length() ?: 0) { i ->
                respondersJson!!.getJSONObject(i).optString("username")
            },

            comments = List(commentsJson?.length() ?: 0) { i ->
                val item = commentsJson!!.getJSONObject(i)
                "${item.optString("author")}: ${item.optString("content")}"
            },

            history = List(historyJson?.length() ?: 0) { i ->
                val item = historyJson!!.getJSONObject(i)
                "${item.optString("action")} — ${item.optString("performed_by")}"
            },

            ownerId = json.optJSONObject("owner")?.optInt("id"),

            myResponse = json.optString("my_response", ""),

            helpRequested = json.optBoolean("help_requested", false),

            createdAt = json.optString("created_at", "")
        )
    }

    fun acknowledgeIncident(token: String, incidentId: Int): String {
        return ApiClient.acknowledgeIncident(token, incidentId)
    }

    fun claimIncident(token: String, incidentId: Int): String {
        return ApiClient.claimIncident(token, incidentId)
    }

    fun joinIncident(token: String, incidentId: Int): String {
        return ApiClient.joinIncident(token, incidentId)
    }

    fun markUnavailable(token: String, id: Int) = ApiClient.markUnavailable(token, id)

    fun requestHelp(token: String, id: Int) = ApiClient.requestHelp(token, id)

    fun resolveIncident(token: String, id: Int) = ApiClient.resolveIncident(token, id)

    fun addComment(token: String, id: Int, content: String) =
        ApiClient.addComment(token, id, content)
}