package com.xmx.ai.chatgpt.viewModel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import com.google.gson.JsonArray
import com.google.gson.JsonObject
import com.xmx.ai.App
import com.xmx.ai.chatgpt.model.GptContent
import com.xmx.ai.chatgpt.model.GptMessage
import com.xmx.ai.chatgpt.repository.GptDatabaseRepository
import com.xmx.ai.chatgpt.repository.GptNetWorkRepository
import com.xmx.ai.database.entity.ContentEntity
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.util.LinkedList

class GptViewModel : ViewModel() {

    private val databaseRepository = GptDatabaseRepository()
    private val netWorkRepository = GptNetWorkRepository()

    private val _prevContent : LinkedList<ContentEntity> = LinkedList<ContentEntity>()

    private var _contentList = MutableLiveData<List<ContentEntity>>()
    val contentList : LiveData<List<ContentEntity>>
        get() = _contentList

    private var _deleteCheck = MutableLiveData(false)
    val deleteCheck : LiveData<Boolean>
        get() = _deleteCheck

    private var _gptInsertCheck = MutableLiveData(false)
    val gptInsertCheck : LiveData<Boolean>
        get() = _gptInsertCheck

    private val _maxContentSize = 8000

    fun postResponse(query : String, isContext : Boolean, system : String, roomId: Long, start: Int) = viewModelScope.launch {

        val message = JsonArray()

        if (system.isNotBlank()) {
            message.add(JsonObject().apply{
                addProperty("role", "system")
                addProperty("content", system)
            })
        }

        if (isContext) {
            val list = ArrayList<JsonObject>()
            var size = 0

            for (item in _prevContent.reversed()) {
                val rest = _maxContentSize - size
                var str = item.content
                var flag = false
                if (str.toByteArray().size > rest)
                {
                    flag = true
                    while (str.length > 1 && str.toByteArray().size > rest)
                    {
                        str = str.substring(0, (str.length * 0.8).toInt())
                    }
                }

                if (item.ai == 1) {
                    list.add(JsonObject().apply{
                        addProperty("role", "assistant")
                        addProperty("content", str)
                    })
                } else {
                    list.add(JsonObject().apply{
                        addProperty("role", "user")
                        addProperty("content", str)
                    })
                }

                size += str.toByteArray().size

                if (flag)
                    break
            }

            for (item in list.reversed()) {
                message.add(item)
            }

            message.add(JsonObject().apply{
                addProperty("role", "user")
                addProperty("content", query)
            })
        } else {
            message.add(JsonObject().apply{
                addProperty("role", "user")
                addProperty("content", query)
            })
        }

        val jsonObject: JsonObject = JsonObject().apply{
            // params
            //addProperty("model", "text-davinci-003")
            addProperty("model", "gpt-3.5-turbo-16k")
            //addProperty("prompt", sb.toString())
            add("messages", message)
            addProperty("temperature", 0.9)
            addProperty("max_tokens", _maxContentSize)
            addProperty("top_p", 1)
            addProperty("frequency_penalty", 0.0)
            addProperty("presence_penalty", 0.0)
            addProperty("stream", false)
        }

        insertContent(query, 2, true, roomId, start)

        try {
            val response = netWorkRepository.postResponse(jsonObject)
            if (response.choices != null) {
                val gson = Gson()
                val tempJson = gson.toJson(response.choices.get(0))
                val tempMessage = gson.fromJson(tempJson, GptMessage::class.java)
                val tempGson = gson.fromJson(tempMessage.massage, GptContent::class.java)
                var extra = ""
                if (response.choices.count() > 1) {
                    val extraJson = gson.toJson(response.choices.get(1))
                    val extraMessage = gson.fromJson(extraJson, GptMessage::class.java)
                    val extraGson = gson.fromJson(extraMessage.massage, GptContent::class.java)
                    if (extraGson.content != null)
                        extra = extraGson.content
                }
                tempGson.content?.let { insertContent(it, 1, true, roomId, 2, extra) }
            }
        } catch (e : Exception) {
            insertContent(e.toString(), 1, false, roomId, 2)
        }

    }

    fun initContentData(roomId: Long) = viewModelScope.launch(Dispatchers.IO) {
        val data = if (roomId > 0)  databaseRepository.getContentDataByRoomId(roomId) else LinkedList<ContentEntity>()
        _contentList.postValue(data)
        _deleteCheck.postValue(false)
        _gptInsertCheck.postValue(false)

        _prevContent.clear()
        _prevContent.addAll(data)
    }

    fun getContentData(roomId: Long) = viewModelScope.launch(Dispatchers.IO) {
        _contentList.postValue(databaseRepository.getContentDataByRoomId(roomId))
        _deleteCheck.postValue(false)
        _gptInsertCheck.postValue(false)
    }

    private fun insertContent(content: String,
                              ai: Int,
                              isContext: Boolean,
                              roomId: Long,
                              start: Int,
                              extra: String = "") = viewModelScope.launch(Dispatchers.IO) {
        val id = databaseRepository.insertContent(content, ai, roomId, start, extra)
        if (ai == 1) {
            // GPT回复
            _gptInsertCheck.postValue(true)
            App.showNotify(2, roomId)
        }
        if (isContext)
            _prevContent.add(ContentEntity(id, roomId, start, 2, content, ai))
    }

    fun deleteSelectedContent(id : Long) = viewModelScope.launch(Dispatchers.IO) {
        databaseRepository.deleteSelectedContent(id)
        _deleteCheck.postValue(true)
    }

}