package com.xmx.ai.bing.viewModel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.JsonObject
import com.xmx.ai.App
import com.xmx.ai.database.entity.ContentEntity
import com.xmx.ai.bing.repository.BingDatabaseRepository
import com.xmx.ai.bing.repository.BingNetWorkRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.LinkedList

class BingViewModel : ViewModel() {

    private val databaseRepository = BingDatabaseRepository()
    private val netWorkRepository = BingNetWorkRepository()
    private var _conversationId = String()
    fun setConversationId(value: String) {
        _conversationId = value
    }

    private var _contentList = MutableLiveData<List<ContentEntity>>()
    val contentList: LiveData<List<ContentEntity>>
        get() = _contentList

    private var _deleteCheck = MutableLiveData(false)
    val deleteCheck: LiveData<Boolean>
        get() = _deleteCheck

    private var _aiInsertCheck = MutableLiveData(false)
    val aiInsertCheck: LiveData<Boolean>
        get() = _aiInsertCheck

    fun postResponse(query: String, isContext: Boolean, style: Int, roomId: Long, start: Int) = viewModelScope.launch {
        val jsonObject: JsonObject = JsonObject().apply {
            addProperty("prompt", query)
            addProperty("style", style)
            addProperty("ref", true)
        }

        if (isContext && _conversationId.isNotBlank()) {
            jsonObject.addProperty("id", _conversationId)
            insertContent(query, 2, _conversationId, roomId, start)
        } else {
            insertContent(query, 2, "", roomId, start)
        }

        try {
            val response = netWorkRepository.postResponse(jsonObject)
            val answer = response.answer ?: ""
            val conversationId = response.conversationId ?: ""
            val extra = response.ref ?: ""
            if (conversationId.isNotBlank())
                _conversationId = conversationId
            insertContent(answer, 1, conversationId, roomId, 2, extra)
        } catch (e: Exception) {
            insertContent(e.toString(), 1, "", roomId, 2)
        }
    }

    fun initContentData(roomId: Long) = viewModelScope.launch(Dispatchers.IO) {
        val data = if (roomId > 0)  databaseRepository.getContentDataByRoomId(roomId) else LinkedList<ContentEntity>()
        _conversationId = ""
        if (data.isNotEmpty()) {
            for (entity in data.reversed()) {
                if (entity.conversationId.isNotBlank()) {
                    _conversationId = entity.conversationId
                    break
                }
            }
        }
        _contentList.postValue(data)
        _deleteCheck.postValue(false)
        _aiInsertCheck.postValue(false)
    }

    fun getContentData(roomId: Long) = viewModelScope.launch(Dispatchers.IO) {
        val data = if (roomId > 0)  databaseRepository.getContentDataByRoomId(roomId) else LinkedList<ContentEntity>()
        _contentList.postValue(data)
        _deleteCheck.postValue(false)
        _aiInsertCheck.postValue(false)
    }

    private fun insertContent(
        content: String,
        ai: Int,
        conversationId: String,
        roomId: Long,
        start: Int,
        extra: String = ""
    ) = viewModelScope.launch(Dispatchers.IO) {
        databaseRepository.insertContent(content, ai, conversationId, roomId, start, extra)
        if (ai == 1) {
            // 回复
            _aiInsertCheck.postValue(true)
            App.showNotify(1, roomId)
        }
    }

    fun deleteSelectedContent(id: Long) = viewModelScope.launch(Dispatchers.IO) {
        databaseRepository.deleteSelectedContent(id)
        _deleteCheck.postValue(true)
    }

}