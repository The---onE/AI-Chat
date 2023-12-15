package com.xmx.ai.gemini.model

import com.google.gson.JsonElement
import com.google.gson.annotations.SerializedName

data class GeminiMessage(
    @SerializedName("message")
    val massage : JsonElement?
)
