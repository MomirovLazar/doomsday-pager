package com.doomsdaypager.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.doomsdaypager.app.ui.theme.DoomsdayPagerTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import androidx.compose.foundation.layout.PaddingValues

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            DoomsdayPagerTheme {

                var username by remember { mutableStateOf("") }
                var password by remember { mutableStateOf("") }
                var passwordVisible by remember { mutableStateOf(false) }

                var loginMessage by remember { mutableStateOf("") }
                var isLoading by remember { mutableStateOf(false) }

                var authToken by remember {
                    mutableStateOf<String?>(null)
                }

                var incidents by remember {
                    mutableStateOf<List<String>>(emptyList())
                }

                val coroutineScope = rememberCoroutineScope()

                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->

                    if (authToken != null) {

                        // INCIDENTS SCREEN

                        LazyColumn(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding),
                            contentPadding = PaddingValues(
                                horizontal = 16.dp, vertical = 20.dp
                            ),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            item {
                                Text(
                                    text = "🚨 ACTIVE INCIDENTS",
                                    style = MaterialTheme.typography.headlineMedium
                                )
                            }

                            items(incidents) { incident ->
                                Card(
                                    modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text(
                                        text = incident,
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(16.dp),
                                        style = MaterialTheme.typography.bodyLarge
                                    )
                                }
                            }

                            if (incidents.isEmpty()) {
                                item {
                                    Text(
                                        text = "No incidents found.",
                                        style = MaterialTheme.typography.bodyMedium
                                    )
                                }
                            }
                        }

                    } else {

                        // LOGIN SCREEN

                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(innerPadding)
                                .imePadding()
                                .verticalScroll(rememberScrollState()),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center
                        ) {

                            Text(
                                text = "🚨 DOOMSDAY PAGER",
                                style = MaterialTheme.typography.headlineMedium
                            )

                            Spacer(
                                modifier = Modifier.height(16.dp)
                            )

                            Text(
                                text = "Emergency Incident Response System"
                            )

                            Spacer(
                                modifier = Modifier.height(24.dp)
                            )

                            OutlinedTextField(
                                value = username,
                                onValueChange = { username = it },
                                label = { Text("Username") },
                                singleLine = true
                            )

                            Spacer(
                                modifier = Modifier.height(12.dp)
                            )

                            OutlinedTextField(
                                value = password,
                                onValueChange = { password = it },
                                label = { Text("Password") },

                                visualTransformation = if (passwordVisible) {
                                    VisualTransformation.None
                                } else {
                                    PasswordVisualTransformation()
                                },

                                trailingIcon = {
                                    IconButton(
                                        onClick = {
                                            passwordVisible = !passwordVisible
                                        }) {
                                        Icon(
                                            imageVector = if (passwordVisible) {
                                                Icons.Filled.VisibilityOff
                                            } else {
                                                Icons.Filled.Visibility
                                            }, contentDescription = if (passwordVisible) {
                                                "Hide password"
                                            } else {
                                                "Show password"
                                            }
                                        )
                                    }
                                },

                                singleLine = true,
                                keyboardOptions = KeyboardOptions(
                                    keyboardType = KeyboardType.Password
                                )
                            )

                            Spacer(
                                modifier = Modifier.height(24.dp)
                            )

                            Button(
                                onClick = {

                                    coroutineScope.launch {

                                        isLoading = true
                                        loginMessage = ""

                                        try {

                                            val token = withContext(Dispatchers.IO) {
                                                loginRequest(username, password)
                                            }

                                            val result = withContext(Dispatchers.IO) {
                                                fetchIncidents(token)
                                            }

                                            val incidentList = mutableListOf<String>()

                                            for (i in 0 until result.length()) {

                                                val incident = result.getJSONObject(i)

                                                incidentList.add(
                                                    "Incident #${incident.optInt("id")}: " + incident.optString(
                                                        "title", "Untitled incident"
                                                    )
                                                )
                                            }

                                            incidents = incidentList
                                            authToken = token
                                            loginMessage = "Login successful!"

                                        } catch (e: Exception) {

                                            loginMessage = "Login failed: ${e.message}"

                                        } finally {

                                            isLoading = false
                                        }
                                    }
                                },

                                enabled = username.isNotBlank() && password.isNotBlank() && !isLoading

                            ) {
                                Text(
                                    if (isLoading) {
                                        "LOGGING IN..."
                                    } else {
                                        "LOGIN"
                                    }
                                )
                            }

                            Spacer(
                                modifier = Modifier.height(16.dp)
                            )

                            Text(loginMessage)
                        }
                    }
                }
            }
        }
    }
}

// HTTP CLIENT

private val httpClient = OkHttpClient()

// LOGIN API

fun loginRequest(
    username: String, password: String
): String {

    val json = JSONObject().apply {
        put("username", username)
        put("password", password)
    }

    val body = json.toString().toRequestBody("application/json".toMediaType())

    val request = Request.Builder().url("http://127.0.0.1:8000/login").post(body).build()

    httpClient.newCall(request).execute().use { response ->

        val responseBody = response.body?.string().orEmpty()

        if (!response.isSuccessful) {
            throw IOException(
                "Login failed: HTTP ${response.code}"
            )
        }

        return JSONObject(responseBody).getString("access_token")
    }
}

// INCIDENTS API

fun fetchIncidents(token: String): JSONArray {

    val request = Request.Builder().url("http://127.0.0.1:8000/incidents")
        .header("Authorization", "Bearer $token").get().build()

    httpClient.newCall(request).execute().use { response ->

        val responseBody = response.body?.string().orEmpty()

        if (!response.isSuccessful) {
            throw IOException(
                "Incidents failed: HTTP ${response.code}"
            )
        }

        return JSONArray(responseBody)
    }
}
