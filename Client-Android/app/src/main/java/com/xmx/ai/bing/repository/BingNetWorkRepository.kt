package com.xmx.ai.bing.repository

import com.google.gson.JsonObject
import com.xmx.ai.bing.network.BingRetrofitInstance
import com.xmx.ai.bing.network.BingApis

class BingNetWorkRepository {

    private val client = BingRetrofitInstance.getInstance().create(BingApis::class.java)

    suspend fun postResponse(jsonData : JsonObject) = client.postRequest(jsonData)
}