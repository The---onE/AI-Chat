package com.xmx.ai.bing.network

import com.google.gson.JsonObject
import com.xmx.ai.bing.model.BingResponse
import retrofit2.http.Body
import retrofit2.http.Headers
import retrofit2.http.POST

interface BingApis {
    @Headers(
        "Content-Type:application/json"
    )
    @POST("api/bing")
    suspend fun postRequest(
        @Body json : JsonObject
    ) : BingResponse

}