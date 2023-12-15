package com.xmx.ai.gemini.model

import com.google.gson.annotations.SerializedName

data class GeminiUploadFileResponse(
    @SerializedName("message")
    val message : String?,

    @SerializedName("index")
    val index : String?
)
