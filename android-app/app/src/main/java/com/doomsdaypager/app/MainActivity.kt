package com.doomsdaypager.app

import android.media.Ringtone
import android.media.RingtoneManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import com.doomsdaypager.app.data.model.Incident
import com.doomsdaypager.app.data.remote.ApiClient
import com.doomsdaypager.app.data.repository.AuthRepository
import com.doomsdaypager.app.data.repository.IncidentRepository
import com.doomsdaypager.app.ui.theme.DoomsdayPagerTheme
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private data class PagerAlarm(val incident: Incident, val help: Boolean) {
    val key: String get() = "${incident.id}:${if (help) "HELP" else "NEW"}"
}

class MainActivity : ComponentActivity() {
    private var ringtone: Ringtone? = null

    private fun startAlarmSound() {
        stopAlarmSound()
        try {
            val uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            ringtone = RingtoneManager.getRingtone(this, uri)
            ringtone?.play()
        } catch (_: Exception) {
            // Alarm screen still appears if the device cannot play sound.
        }
    }

    private fun stopAlarmSound() {
        try {
            ringtone?.stop()
        } catch (_: Exception) {
        }
        ringtone = null
    }

    override fun onStop() {
        super.onStop()
        stopAlarmSound()
    }

    override fun onDestroy() {
        stopAlarmSound()
        super.onDestroy()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        setContent {
            DoomsdayPagerTheme {
                val repository = remember { IncidentRepository() }
                val scope = rememberCoroutineScope()

                var username by remember { mutableStateOf("") }
                var password by remember { mutableStateOf("") }
                var passwordVisible by remember { mutableStateOf(false) }
                var token by remember { mutableStateOf<String?>(null) }
                var userRole by remember { mutableStateOf("") }
                var loading by remember { mutableStateOf(false) }
                var message by remember { mutableStateOf("") }
                var incidents by remember { mutableStateOf<List<Incident>>(emptyList()) }
                var alarm by remember { mutableStateOf<PagerAlarm?>(null) }
                var confirmed by remember { mutableStateOf(false) }
                var confirmedAction by remember { mutableStateOf("") }
                var busy by remember { mutableStateOf(false) }
                var pending by remember { mutableStateOf<List<PagerAlarm>>(emptyList()) }
                var seenKeys by remember { mutableStateOf<Set<String>>(emptySet()) }
                var initialized by remember { mutableStateOf(false) }

                fun showNext() {
                    val next = pending.firstOrNull()
                    pending = pending.drop(1)
                    alarm = next
                    confirmed = false
                    confirmedAction = ""
                    if (next != null) startAlarmSound() else stopAlarmSound()
                }

                // Polling only while this Activity is running. It is NOT background push.
                LaunchedEffect(token, userRole) {
                    val auth = token ?: return@LaunchedEffect
                    if (userRole != "SYSTEM_ADMIN" && userRole != "ADMIN") return@LaunchedEffect
                    while (isActive) {
                        try {
                            val latest = withContext(Dispatchers.IO) {
                                repository.getIncidents(auth)
                            }
                            val detailed = withContext(Dispatchers.IO) {
                                latest.map { item ->
                                    try {
                                        repository.getIncidentDetails(auth, item.id)
                                    } catch (_: Exception) {
                                        item
                                    }
                                }
                            }
                            incidents = detailed

                            val candidates =
                                detailed.filter { it.status != "RESOLVED" }.mapNotNull { item ->
                                    if (item.helpRequested || item.status == "NEW") {
                                        PagerAlarm(item, item.helpRequested)
                                    } else null
                                }
                            val candidateKeys = candidates.map { it.key }.toSet()
                            if (!initialized) {
                                // Existing incidents at login do not trigger a surprise alarm.
                                seenKeys = candidateKeys
                                initialized = true
                            } else {
                                val fresh = candidates.filter { it.key !in seenKeys }
                                seenKeys = seenKeys + candidateKeys
                                if (fresh.isNotEmpty()) {
                                    pending = pending + fresh
                                    if (alarm == null) showNext()
                                }
                            }
                        } catch (e: Exception) {
                            message = "Refresh failed: ${e.message}"
                        }
                        delay(8000L)
                    }
                }

                Scaffold(modifier = Modifier.fillMaxSize()) { padding ->
                    if (token == null) {
                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(padding)
                                .padding(24.dp)
                                .imePadding()
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.Center,
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                "🚨 DOOMSDAY PAGER", style = MaterialTheme.typography.headlineMedium
                            )
                            Spacer(Modifier.height(12.dp))
                            Text("Emergency Incident Response System")
                            Spacer(Modifier.height(24.dp))
                            OutlinedTextField(
                                value = username,
                                onValueChange = { username = it },
                                label = { Text("Username") },
                                singleLine = true
                            )
                            Spacer(Modifier.height(12.dp))
                            OutlinedTextField(
                                value = password,
                                onValueChange = { password = it },
                                label = { Text("Password") },
                                singleLine = true,
                                visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                                trailingIcon = {
                                    IconButton(onClick = { passwordVisible = !passwordVisible }) {
                                        Icon(
                                            if (passwordVisible) Icons.Filled.VisibilityOff
                                            else Icons.Filled.Visibility,
                                            contentDescription = "Toggle password visibility"
                                        )
                                    }
                                })
                            Spacer(Modifier.height(20.dp))
                            Button(
                                enabled = !loading && username.isNotBlank() && password.isNotBlank(),
                                onClick = {
                                    scope.launch {
                                        loading = true
                                        message = ""
                                        try {
                                            val auth = withContext(Dispatchers.IO) {
                                                AuthRepository().login(username.trim(), password)
                                            }
                                            val me = withContext(Dispatchers.IO) {
                                                ApiClient.getMe(auth)
                                            }
                                            val list = withContext(Dispatchers.IO) {
                                                repository.getIncidents(auth).map { item ->
                                                    try {
                                                        repository.getIncidentDetails(auth, item.id)
                                                    } catch (_: Exception) {
                                                        item
                                                    }
                                                }
                                            }
                                            userRole = me.optString("role")
                                            incidents = list
                                            initialized = false
                                            seenKeys = emptySet()
                                            pending = emptyList()
                                            alarm = null
                                            token = auth
                                        } catch (e: Exception) {
                                            message = "Login failed: ${e.message}"
                                        } finally {
                                            loading = false
                                        }
                                    }
                                }) { Text(if (loading) "LOGGING IN..." else "LOGIN") }
                            if (message.isNotBlank()) {
                                Spacer(Modifier.height(12.dp))
                                Text(message)
                            }
                        }
                    } else if (alarm != null) {
                        val active = alarm!!
                        val item = active.incident
                        val canClaim = !active.help && item.status == "NEW" && item.owner.isBlank()
                        val canRespond =
                            item.myResponse != "ACKNOWLEDGED" && item.myResponse != "UNAVAILABLE"

                        Column(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(padding)
                                .padding(20.dp)
                                .verticalScroll(rememberScrollState()),
                            verticalArrangement = Arrangement.Center
                        ) {
                            if (confirmed) {
                                Text(
                                    "✓",
                                    color = Color(0xFF32D583),
                                    style = MaterialTheme.typography.displayMedium,
                                    modifier = Modifier.align(Alignment.CenterHorizontally)
                                )
                                Spacer(Modifier.height(18.dp))
                                Text(
                                    when (confirmedAction) {
                                        "ack" -> "Incident acknowledged"
                                        "claim" -> "Incident assigned to you"
                                        "unavailable" -> "Availability response recorded"
                                        else -> "Response recorded"
                                    },
                                    fontWeight = FontWeight.Bold,
                                    style = MaterialTheme.typography.headlineSmall,
                                    modifier = Modifier.align(Alignment.CenterHorizontally)
                                )
                                Spacer(Modifier.height(12.dp))
                                Text(
                                    when (confirmedAction) {
                                        "ack" -> "You can continue monitoring incidents."
                                        "claim" -> "Please switch to your PC to continue working on this incident."
                                        "unavailable" -> "You are marked as unavailable for this incident."
                                        else -> "Your response has been recorded."
                                    }, modifier = Modifier.align(Alignment.CenterHorizontally)
                                )
                                Spacer(Modifier.height(24.dp))
                                Button(
                                    onClick = { showNext() }, modifier = Modifier.fillMaxWidth()
                                ) {
                                    Text("BACK TO INCIDENTS")
                                }
                            } else {
                                Text(
                                    if (active.help) "🚨 ADDITIONAL HELP REQUESTED"
                                    else "🚨 ${item.priority.ifBlank { "NEW" }} INCIDENT",
                                    color = Color(0xFFFF6464),
                                    fontWeight = FontWeight.Bold,
                                    style = MaterialTheme.typography.titleLarge
                                )
                                Spacer(Modifier.height(20.dp))
                                Text(
                                    item.title,
                                    style = MaterialTheme.typography.headlineMedium,
                                    fontWeight = FontWeight.Bold
                                )
                                Spacer(Modifier.height(12.dp))
                                Text(item.description.ifBlank { "No description provided." })
                                Spacer(Modifier.height(16.dp))
                                Text("Incident #${item.id}  •  ${item.status}")
                                if (active.help) {
                                    Spacer(Modifier.height(8.dp))
                                    Text("Owner: ${item.owner.ifBlank { "Unknown" }}")
                                }
                                HorizontalDivider(modifier = Modifier.padding(vertical = 20.dp))
                                fun submit(action: String) {
                                    val auth = token ?: return
                                    scope.launch {
                                        busy = true
                                        message = ""
                                        try {
                                            withContext(Dispatchers.IO) {
                                                when (action) {
                                                    "claim" -> repository.claimIncident(
                                                        auth, item.id
                                                    )

                                                    "ack" -> repository.acknowledgeIncident(
                                                        auth, item.id
                                                    )

                                                    else -> repository.markUnavailable(
                                                        auth, item.id
                                                    )
                                                }
                                            }
                                            stopAlarmSound()
                                            confirmedAction = action
                                            confirmed = true
                                            // Avoid immediately replaying the same event.
                                            seenKeys = seenKeys + active.key
                                        } catch (e: Exception) {
                                            message = "Action failed: ${e.message}"
                                        } finally {
                                            busy = false
                                        }
                                    }
                                }
                                Button(
                                    onClick = { submit("claim") },
                                    enabled = !busy && canClaim,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("ASSIGN ME") }
                                Spacer(Modifier.height(8.dp))
                                Button(
                                    onClick = { submit("ack") },
                                    enabled = !busy && canRespond,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("ACKNOWLEDGE") }
                                Spacer(Modifier.height(8.dp))
                                OutlinedButton(
                                    onClick = { submit("unavailable") },
                                    enabled = !busy && canRespond,
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text("UNAVAILABLE") }
                                if (active.help) {
                                    Spacer(Modifier.height(8.dp))
                                    Text("This incident already has an owner. Continue on PC.")
                                }
                                if (message.isNotBlank()) {
                                    Spacer(Modifier.height(12.dp))
                                    Text(message, color = MaterialTheme.colorScheme.error)
                                }
                                Spacer(Modifier.height(16.dp))
                                TextButton(onClick = {
                                    stopAlarmSound()
                                    showNext()
                                }) { Text("VIEW INCIDENT LIST") }
                            }
                        }
                    } else {
                        LazyColumn(
                            modifier = Modifier
                                .fillMaxSize()
                                .padding(padding),
                            contentPadding = PaddingValues(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            item {
                                Text(
                                    "🚨 DOOMSDAY PAGER",
                                    style = MaterialTheme.typography.headlineMedium
                                )
                                Text("INCIDENT OVERVIEW")
                                Spacer(Modifier.height(12.dp))
                                Row {
                                    OutlinedButton(onClick = {
                                        val auth = token ?: return@OutlinedButton
                                        scope.launch {
                                            try {
                                                incidents = withContext(Dispatchers.IO) {
                                                    repository.getIncidents(auth).map { item ->
                                                        try {
                                                            repository.getIncidentDetails(
                                                                auth, item.id
                                                            )
                                                        } catch (_: Exception) {
                                                            item
                                                        }
                                                    }
                                                }
                                                message = ""
                                            } catch (e: Exception) {
                                                message = "Refresh failed: ${e.message}"
                                            }
                                        }
                                    }) { Text("REFRESH") }
                                    Spacer(Modifier.width(12.dp))
                                    OutlinedButton(onClick = {
                                        stopAlarmSound()
                                        token = null
                                        userRole = ""
                                        incidents = emptyList()
                                        pending = emptyList()
                                        seenKeys = emptySet()
                                        initialized = false
                                    }) { Text("LOG OUT") }
                                }
                                if (message.isNotBlank()) Text(message)
                            }
                            items(incidents, key = { it.id }) { item ->
                                Card(modifier = Modifier.fillMaxWidth()) {
                                    Column(modifier = Modifier.padding(16.dp)) {
                                        Text(
                                            "#${item.id}  ${item.title}",
                                            fontWeight = FontWeight.Bold
                                        )
                                        Spacer(Modifier.height(6.dp))
                                        Text("${item.priority}  •  ${item.status}")
                                        Spacer(Modifier.height(6.dp))
                                        Text("Owner: ${item.owner.ifBlank { "Unassigned" }}")
                                    }
                                }
                            }
                            if (incidents.isEmpty()) {
                                item { Text("No incidents found.") }
                            }
                        }
                    }
                }
            }
        }
    }
}
