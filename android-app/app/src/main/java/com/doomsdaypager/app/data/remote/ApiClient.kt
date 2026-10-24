package com.doomsdaypager.app.data.remote

import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

object ApiClient {

    private const val BASE_URL = "http://10.131.152.90:8000"

    private val client = OkHttpClient.Builder().connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS).build()

    fun login(username: String, password: String): String {
        val body = JSONObject().apply {
            put("username", username)
            put("password", password)
        }.toString().toRequestBody(
            "application/json".toMediaType()
        )

        val request = Request.Builder().url("$BASE_URL/login").post(body).build()

        client.newCall(request).execute().use { response ->
            val responseBody = response.body?.string().orEmpty()

            if (!response.isSuccessful) {
                throw IOException("Login failed: HTTP ${response.code}")
            }

            return JSONObject(responseBody).getString("access_token")
        }
    }

    fun getIncidents(token: String): JSONArray {
        val request =
            Request.Builder().url("$BASE_URL/incidents").header("Authorization", "Bearer $token")
                .get().build()

        client.newCall(request).execute().use { response ->
            val responseBody = response.body?.string().orEmpty()

            if (!response.isSuccessful) {
                throw IOException("Incidents failed: HTTP ${response.code}")
            }

            return JSONArray(responseBody)
        }
    }

    fun acknowledgeIncident(token: String, incidentId: Int): String {
        val request = Request.Builder().url("$BASE_URL/incidents/$incidentId/acknowledge")
            .header("Authorization", "Bearer $token").post(ByteArray(0).toRequestBody(null)).build()

        client.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()

            if (!response.isSuccessful) {
                throw okio.IOException(
                    "ACK failed: HTTP ${response.code} - $body"
                )
            }

            return JSONObject(body).optString(
                "message", "Incident acknowledged successfully"
            )
        }
    }

    fun getIncidentDetails(token: String, incidentId: Int): JSONObject {
        val request = Request.Builder().url("$BASE_URL/incidents/$incidentId")
            .header("Authorization", "Bearer $token").get().build()

        client.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()

            if (!response.isSuccessful) {
                throw IOException(
                    "Details failed: HTTP ${response.code} - $body"
                )
            }

            return JSONObject(body)
        }
    }

    fun claimIncident(token: String, incidentId: Int): String {
        return postIncidentAction(token, incidentId, "claim")
    }

    fun joinIncident(token: String, incidentId: Int): String {
        return postIncidentAction(token, incidentId, "join")
    }

    fun getMe(token: String): JSONObject {
        val request =
            Request.Builder().url("$BASE_URL/me").header("Authorization", "Bearer $token").get()
                .build()

        client.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("GET /me: HTTP ${response.code} - $body")
            }
            return JSONObject(body)
        }
    }

    fun markUnavailable(token: String, incidentId: Int): String =
        postIncidentAction(token, incidentId, "unavailable")

    fun requestHelp(token: String, incidentId: Int): String =
        postIncidentAction(token, incidentId, "request-help")

    fun resolveIncident(token: String, incidentId: Int): String =
        postIncidentAction(token, incidentId, "resolve")

    fun addComment(token: String, incidentId: Int, content: String) {
        val body = JSONObject().put("content", content.trim()).toString()
            .toRequestBody("application/json".toMediaType())

        val request = Request.Builder().url("$BASE_URL/incidents/$incidentId/comments")
            .header("Authorization", "Bearer $token").post(body).build()

        client.newCall(request).execute().use { response ->
            val result = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("Comment: HTTP ${response.code} - $result")
            }
        }
    }

    private fun postIncidentAction(
        token: String, incidentId: Int, action: String
    ): String {
        val request = Request.Builder().url("$BASE_URL/incidents/$incidentId/$action")
            .header("Authorization", "Bearer $token").post(ByteArray(0).toRequestBody(null)).build()

        client.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()

            if (!response.isSuccessful) {
                throw IOException(
                    "HTTP ${response.code}: $body"
                )
            }

            return JSONObject(body).optString(
                "message", "Action completed successfully"
            )
        }
    }
}