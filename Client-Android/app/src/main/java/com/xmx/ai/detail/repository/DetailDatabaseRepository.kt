package com.xmx.ai.detail.repository

import com.xmx.ai.App
import com.xmx.ai.database.ChatDatabase

class DetailDatabaseRepository {

    private val context = App.context()
    private val database = ChatDatabase.getDatabase(context)

    fun getContentData(id: Long) = database.contentDAO().getContentData(id)

}