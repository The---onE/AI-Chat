package com.xmx.ai.list.viewModel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmx.ai.database.entity.ContentEntity
import com.xmx.ai.list.repository.ListDatabaseRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class ListViewModel : ViewModel() {

    private val databaseRepository = ListDatabaseRepository()

    private var _contentList = MutableLiveData<List<ContentEntity>>()
    val contentList: LiveData<List<ContentEntity>>
        get() = _contentList

    private var _deleteCheck = MutableLiveData(false)
    val deleteCheck: LiveData<Boolean>
        get() = _deleteCheck

    fun initContentData() = viewModelScope.launch(Dispatchers.IO) {
        _contentList.postValue(databaseRepository.getAllStartContentData())
        _deleteCheck.postValue(false)
    }

    fun getContentData() = viewModelScope.launch(Dispatchers.IO) {
        _contentList.postValue(databaseRepository.getAllStartContentData())
        _deleteCheck.postValue(false)
    }

    fun deleteSelectedContent(roomId: Long) = viewModelScope.launch(Dispatchers.IO) {
        databaseRepository.deleteRoomContent(roomId)
        _deleteCheck.postValue(true)
    }

    fun deleteAllContent() = viewModelScope.launch(Dispatchers.IO) {
        databaseRepository.deleteAllContent()
        _deleteCheck.postValue(true)
    }

}