package com.xmx.ai.detail.viewModel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.xmx.ai.database.entity.ContentEntity
import com.xmx.ai.detail.repository.DetailDatabaseRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class DetailViewModel : ViewModel() {

    private val databaseRepository = DetailDatabaseRepository()

    private var _contentList = MutableLiveData<List<ContentEntity>>()
    val contentList: LiveData<List<ContentEntity>>
        get() = _contentList

    fun initContentData(id: Long) = viewModelScope.launch(Dispatchers.IO) {
        _contentList.postValue(databaseRepository.getContentData(id))
    }

}