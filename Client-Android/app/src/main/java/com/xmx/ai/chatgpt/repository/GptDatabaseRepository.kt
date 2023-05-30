package com.xmx.ai.chatgpt.repository

import com.xmx.ai.App
import com.xmx.ai.database.ChatDatabase
import com.xmx.ai.database.entity.ContentEntity

class GptDatabaseRepository {

    private val context = App.context()
    private val database = ChatDatabase.getDatabase(context)

    fun getContentDataByRoomId(roomId: Long) = database.contentDAO().getContentDataByRoomId(roomId)

    fun insertContent(
        content: String,
        user: Int,
        roomId: Long,
        start: Int
    ) = database.contentDAO()
        .insertContent(ContentEntity(0, roomId, start, 2, content, user, ""))

    fun deleteSelectedContent(id : Long) = database.contentDAO().deleteSelectedContent(id)

}