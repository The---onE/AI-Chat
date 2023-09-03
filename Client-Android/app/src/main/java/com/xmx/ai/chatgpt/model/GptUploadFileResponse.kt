package com.xmx.ai.chatgpt.model

import com.google.gson.annotations.SerializedName

data class GptUploadFileResponse(
    @SerializedName("message")
    val message : String?,

    @SerializedName("index")
    val index : String?
)
