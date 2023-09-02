package com.xmx.ai.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import com.xmx.ai.database.entity.ContentEntity

@Dao
interface ContentDAO {

    @Query("SELECT * FROM ContentTable")
    fun getAllContentData() : List<ContentEntity>

    @Query("SELECT * FROM ContentTable WHERE Id = :Id")
    fun getContentData(Id: Long) : List<ContentEntity>

    @Query("SELECT * FROM ContentTable WHERE roomId = :roomId ORDER BY id")
    fun getContentDataByRoomId(roomId: Long) : List<ContentEntity>

    @Query("SELECT * FROM ContentTable WHERE start = 1 ORDER BY id DESC LIMIT :limit OFFSET :offset")
    fun getAllStartContentData(limit: Int, offset: Int) : List<ContentEntity>

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    fun insertContent(content : ContentEntity) : Long

    @Query("DELETE FROM ContentTable WHERE id = :id")
    fun deleteSelectedContent(id : Long)

    @Query("DELETE FROM ContentTable WHERE roomId = :roomId")
    fun deleteRoomContent(roomId : Long)

    @Query("DELETE FROM ContentTable")
    fun deleteAllContent()

}