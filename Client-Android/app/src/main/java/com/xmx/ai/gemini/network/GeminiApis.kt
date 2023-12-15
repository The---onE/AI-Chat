package com.xmx.ai.gemini.network

import com.google.gson.JsonObject
import com.xmx.ai.gemini.model.GeminiResponse
import com.xmx.ai.gemini.model.GeminiUploadFileResponse
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.Headers
import retrofit2.http.POST

interface GeminiApis {
    @Headers(
        "Content-Type:application/json"
    )
    @POST("api/gemini")
    suspend fun postRequest(
        @Body json : JsonObject
    ) : GeminiResponse

    @POST("file")
    suspend fun uploadFileRequest(
        @Body json : MultipartBody
    ) : GeminiUploadFileResponse
}