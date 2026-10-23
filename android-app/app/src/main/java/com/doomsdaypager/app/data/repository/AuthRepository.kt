package com.doomsdaypager.app.data.repository

import com.doomsdaypager.app.data.remote.ApiClient

class AuthRepository {

    fun login(username: String, password: String): String {
        return ApiClient.login(username, password)
    }
}