package com.xmx.ai.gemini.repository

import com.google.gson.JsonObject
import com.xmx.ai.gemini.network.GeminiApis
import com.xmx.ai.gemini.network.GeminiRetrofitInstance
import okhttp3.MultipartBody

class GeminiNetWorkRepository {

    private val client = GeminiRetrofitInstance.getInstance().create(GeminiApis::class.java)

    suspend fun postResponse(jsonData : JsonObject) = client.postRequest(jsonData)

    suspend fun uploadFileResponse(jsonData : MultipartBody) = client.uploadFileRequest(jsonData)
}