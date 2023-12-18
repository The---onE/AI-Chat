package com.xmx.ai.chatgpt.network

import com.xmx.ai.utils.NetworkUtil
import retrofit2.Retrofit

object GptRetrofitInstance {
    private const val BASE_URL = "[Server Address]"

    private val client = NetworkUtil.makeClient(BASE_URL)

    fun getInstance(): Retrofit {
        return client
    }
}