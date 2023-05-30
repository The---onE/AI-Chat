package com.xmx.ai.chatgpt.model

import com.google.gson.JsonElement
import com.google.gson.annotations.SerializedName

data class GptMessage(
    @SerializedName("message")
    val massage : JsonElement?
)
