package com.xmx.ai.chatgpt.network

import com.google.gson.JsonObject
import com.xmx.ai.chatgpt.model.GptResponse
import com.xmx.ai.chatgpt.model.GptUploadFileResponse
import okhttp3.MultipartBody
import retrofit2.http.Body
import retrofit2.http.Headers
import retrofit2.http.POST

interface GptApis {
    @Headers(
        "Content-Type:application/json",
//        "Authorization:Bearer api-key"
    )
    @POST("api/chatgpt")
    suspend fun postRequest(
        @Body json : JsonObject
    ) : GptResponse

    @POST("file")
    suspend fun uploadFileRequest(
        @Body json : MultipartBody
    ) : GptUploadFileResponse
}