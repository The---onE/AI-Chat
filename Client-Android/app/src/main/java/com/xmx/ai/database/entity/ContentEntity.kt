package com.xmx.ai.database.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "ContentTable")
data class ContentEntity(

    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "id")
    var id : Long,

    @ColumnInfo(name = "roomId")
    var roomId : Long,

    @ColumnInfo(name = "start")
    var start : Int,

    @ColumnInfo(name = "roomType")
    var roomType : Int,

    @ColumnInfo(name = "content")
    var content : String,

    @ColumnInfo(name = "ai")
    var ai : Int,

    @ColumnInfo(name = "conversationId", defaultValue = "")
    var conversationId : String = "",

    @ColumnInfo(name = "extra", defaultValue = "")
    var extra : String = ""

)