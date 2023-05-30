package com.xmx.ai.list.repository

import com.xmx.ai.App
import com.xmx.ai.database.ChatDatabase

class ListDatabaseRepository {

    private val context = App.context()
    private val database = ChatDatabase.getDatabase(context)

    fun getAllStartContentData() = database.contentDAO().getAllStartContentData()

    fun deleteRoomContent(roomId: Long) = database.contentDAO().deleteRoomContent(roomId)

    fun deleteAllContent() = database.contentDAO().deleteAllContent()

}