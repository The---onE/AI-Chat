package com.xmx.ai.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.xmx.ai.database.dao.ContentDAO
import com.xmx.ai.database.entity.ContentEntity

@Database(entities = [ContentEntity::class], version = 2)
abstract class ChatDatabase : RoomDatabase() {

    abstract fun contentDAO() : ContentDAO

    companion object {
        @Volatile
        private var INSTANCE : ChatDatabase? = null

        fun getDatabase(
            context : Context
        ) : ChatDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    ChatDatabase::class.java,
                    "chatDatabase"
                )
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}