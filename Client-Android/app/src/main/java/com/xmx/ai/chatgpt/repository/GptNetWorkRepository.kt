package com.xmx.ai.chatgpt.repository

import com.google.gson.JsonObject
import com.xmx.ai.chatgpt.network.GptApis
import com.xmx.ai.chatgpt.network.GptRetrofitInstance
import okhttp3.MultipartBody

class GptNetWorkRepository {

    private val chatGPTClient = GptRetrofitInstance.getInstance().create(GptApis::class.java)

    suspend fun postResponse(jsonData : JsonObject) = chatGPTClient.postRequest(jsonData)

    suspend fun uploadFileResponse(jsonData : MultipartBody) = chatGPTClient.uploadFileRequest(jsonData)
}