package com.xmx.ai.gemini.model

import com.google.gson.annotations.SerializedName

data class GeminiContent(
    @SerializedName("content")
    val content : String?
)
