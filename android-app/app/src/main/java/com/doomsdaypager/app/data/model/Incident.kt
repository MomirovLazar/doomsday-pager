package com.doomsdaypager.app.data.model

data class Incident(
    val id: Int,
    val title: String,
    val description: String = "",
    val status: String = "",
    val priority: String = "",
    val type: String = "",
    val createdBy: String = "",
    val owner: String = "",
    val responders: List<String> = emptyList(),
    val comments: List<String> = emptyList(),
    val history: List<String> = emptyList(),
    val ownerId: Int? = null,
    val myResponse: String = "",
    val helpRequested: Boolean = false,
    val createdAt: String = ""
)