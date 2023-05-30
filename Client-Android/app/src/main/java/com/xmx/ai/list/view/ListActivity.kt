package com.xmx.ai.list.view

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.ScrollView
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import com.xmx.ai.App
import com.xmx.ai.bing.view.BingActivity
import com.xmx.ai.chatgpt.view.GptActivity
import com.xmx.ai.database.entity.ContentEntity
import com.xmx.ai.databinding.ActivityListBinding
import com.xmx.ai.list.adapter.ListContentAdapter
import com.xmx.ai.list.viewModel.ListViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlin.system.exitProcess

class ListActivity : AppCompatActivity() {

    private lateinit var binding : ActivityListBinding
    private val viewModel : ListViewModel by viewModels()
    private var contentDataList = ArrayList<ContentEntity>()
    var isActive : Boolean = false

    init {
        instance = this
    }
    companion object {
        var instance : ListActivity? = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {

        installSplashScreen()

        super.onCreate(savedInstanceState)

        App.createChannel()

        binding = ActivityListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        viewModel.initContentData()

        viewModel.contentList.observe(this) {
            contentDataList.clear()
            for (entity in it) {
                contentDataList.add(entity)
            }
            setContentListRV()
        }

        viewModel.deleteCheck.observe(this) {
            if (it == true) {
                viewModel.getContentData()
            }
        }

        binding.newBingBtn.setOnClickListener {
            val intent = Intent(this@ListActivity, BingActivity::class.java)
            startActivity(intent)
        }

        binding.newGptBtn.setOnClickListener {
            val intent = Intent(this@ListActivity, GptActivity::class.java)
            startActivity(intent)
        }
    }

    override fun onResume() {
        super.onResume()
        isActive = true
        viewModel.getContentData()
    }

    override fun onPause() {
        super.onPause()
        isActive = false
    }

    private var exitTime: Long = 0
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (System.currentTimeMillis() - exitTime > 2000) {
            binding.SVList.fullScroll(ScrollView.FOCUS_UP)
            exitTime = System.currentTimeMillis();
        }else {
            finish()
            BingActivity.instance?.finish()
            GptActivity.instance?.finish()
        }
    }

    private fun setContentListRV() {
        val contentAdapter = ListContentAdapter(this, contentDataList)
        binding.RVList.adapter = contentAdapter
        binding.RVList.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        CoroutineScope(Dispatchers.Main).launch {
//            delay(100)
//            binding.SVList.fullScroll(ScrollView.FOCUS_UP)
        }

        contentAdapter.listLayoutClick = object : ListContentAdapter.ListLayoutClick {
            override fun onLongClick(view : View, position: Int) {
                val builder = AlertDialog.Builder(this@ListActivity)
                builder.setTitle("删除消息")
                    .setMessage("删除的消息无法恢复。")
                    .setPositiveButton("确定") { _, _ ->
                        viewModel.deleteSelectedContent(contentDataList[position].roomId)
                    }
                    .setNegativeButton("取消") { _, _ ->
                    }
                builder.show()
            }

            override fun onClick(view: View, position: Int) {
                val entity = contentDataList[position]
                val intent =
                    if (entity.roomType == 1) Intent(this@ListActivity, BingActivity::class.java)
                    else Intent(this@ListActivity, GptActivity::class.java)
                intent.putExtra("roomId", contentDataList[position].roomId)
                startActivity(intent)
            }
        }
    }
}