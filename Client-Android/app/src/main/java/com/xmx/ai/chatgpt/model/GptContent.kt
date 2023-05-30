package com.xmx.ai.chatgpt.model

import com.google.gson.annotations.SerializedName

data class GptContent(
    @SerializedName("content")
    val content : String?
)
