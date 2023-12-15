package com.xmx.ai.gemini.repository

import com.xmx.ai.App
import com.xmx.ai.database.ChatDatabase
import com.xmx.ai.database.entity.ContentEntity

class GeminiDatabaseRepository {

    private val context = App.context()
    private val database = ChatDatabase.getDatabase(context)

    fun getContentDataByRoomId(roomId: Long) = database.contentDAO().getContentDataByRoomId(roomId)

    fun insertContent(
        content: String,
        user: Int,
        roomId: Long,
        start: Int,
        extra: String = ""
    ) = database.contentDAO()
        .insertContent(ContentEntity(0, roomId, start, 3, content, user, "", extra))

    fun deleteSelectedContent(id : Long) = database.contentDAO().deleteSelectedContent(id)

}