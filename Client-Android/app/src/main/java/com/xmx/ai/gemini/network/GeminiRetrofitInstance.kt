package com.xmx.ai.gemini.network

import com.xmx.ai.utils.NetworkUtil
import retrofit2.Retrofit

object GeminiRetrofitInstance {
    private const val BASE_URL = "[Server Address]"

    private val client = NetworkUtil.makeClient(BASE_URL)

    fun getInstance(): Retrofit {
        return client
    }
}