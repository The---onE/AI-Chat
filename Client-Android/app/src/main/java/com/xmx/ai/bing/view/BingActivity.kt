package com.xmx.ai.bing.view

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Build.VERSION.SDK_INT
import android.os.Bundle
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.RadioButton
import android.widget.ScrollView
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.children
import androidx.recyclerview.widget.LinearLayoutManager
import coil.Coil
import coil.ImageLoader
import coil.decode.GifDecoder
import coil.decode.ImageDecoderDecoder
import coil.load
import com.xmx.ai.R
import com.xmx.ai.bing.adapter.BingContentAdapter
import com.xmx.ai.database.entity.ContentEntity
import com.xmx.ai.bing.viewModel.BingViewModel
import com.xmx.ai.databinding.ActivityBingBinding
import com.xmx.ai.detail.view.DetailActivity
import com.xmx.ai.list.view.ListActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.lang.Thread.sleep

class BingActivity : AppCompatActivity() {

    private lateinit var binding : ActivityBingBinding
    private val viewModel : BingViewModel by viewModels()
    private var contentDataList = ArrayList<ContentEntity>()
    private var roomId : Long = -1
    var isActive : Boolean = false

    init {
        instance = this
    }
    companion object {
        var instance : BingActivity? = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)

        roomId = intent.getLongExtra("roomId", 0)

        binding = ActivityBingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val imageLoader = this.let {
            ImageLoader.Builder(it)
                .components {
                    if (SDK_INT >= 28) {
                        add(ImageDecoderDecoder.Factory())
                    } else {
                        add(GifDecoder.Factory())
                    }
                }
                .build()
        }
        Coil.setImageLoader(imageLoader)
        binding.loading.visibility = View.INVISIBLE
        binding.loading.load(R.drawable.loading3)

        viewModel.initContentData(roomId)

        viewModel.contentList.observe(this) {
            contentDataList.clear()
            for (entity in it) {
                contentDataList.add(entity)
            }
            setContentListRV()
        }

        viewModel.deleteCheck.observe(this) {
            if (it == true) {
                viewModel.getContentData(roomId)
            }
        }

        viewModel.aiInsertCheck.observe(this) {
            if (it == true) {
                viewModel.getContentData(roomId)
                binding.loading.visibility = View.INVISIBLE
            }
        }

//        binding.backBtn.setOnLongClickListener {
//            viewModel.deleteAllContent()
//            return@setOnLongClickListener true
//        }

        binding.backBtn.setOnClickListener {
            val intent = Intent(this, ListActivity::class.java)
            startActivity(intent)
        }

        binding.sendBtn.setOnClickListener {
            postRequest(true)
        }

        binding.sendBtn.setOnLongClickListener {
            postRequest(false)
            return@setOnLongClickListener true
        }

        binding.EDView.onFocusChangeListener = View.OnFocusChangeListener {
                _, hasFocus ->
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            if (hasFocus) {
                imm.showSoftInput(binding.EDView, InputMethodManager.SHOW_IMPLICIT)
            }else {
                imm.hideSoftInputFromWindow(binding.EDView.windowToken, 0)
            }
        }
    }

    override fun onResume() {
        super.onResume()
        isActive = true
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)

        roomId = intent?.getLongExtra("roomId", 0) ?: 0
        viewModel.initContentData(roomId)
    }

    override fun onPause() {
        super.onPause()
        isActive = false
    }

    private var exitTime: Long = 0
    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (System.currentTimeMillis() - exitTime > 2000) {
            binding.SVContainer.fullScroll(ScrollView.FOCUS_DOWN)
            exitTime = System.currentTimeMillis()
        }else {
            val intent = Intent(this, ListActivity::class.java)
            startActivity(intent)
        }
    }

    private fun postRequest(isContext : Boolean) {
        val query = binding.EDView.text.toString()
        if (query.isBlank())
            return

        if (isContext && binding.loading.visibility == View.VISIBLE)
            return

        binding.loading.visibility = View.VISIBLE

        var style = 1
        for (child in binding.StyleRadio.children) {
            val button = child as RadioButton
            if (button.isChecked) {
                when (button.id) {
                    R.id.radio_creative->
                        style = 1
                    R.id.radio_balanced->
                        style = 2
                    R.id.radio_precise->
                        style = 3
                }
                break
            }
        }


        var start = 2
        if (roomId <= 0) {
            roomId = System.currentTimeMillis()
            start = 1
        }

        viewModel.postResponse(query, isContext, style, roomId, start)
        binding.EDView.setText("")
        sleep(100)
        viewModel.getContentData(roomId)
        binding.SVContainer.fullScroll(ScrollView.FOCUS_DOWN)
    }

    private fun setContentListRV() {
        val contentAdapter = BingContentAdapter(this, contentDataList)
        binding.RVContainer.adapter = contentAdapter
        binding.RVContainer.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }
        CoroutineScope(Dispatchers.Main).launch {
            delay(100)
            binding.SVContainer.fullScroll(ScrollView.FOCUS_DOWN)
        }

        contentAdapter.chatLayoutClick = object : BingContentAdapter.ChatLayoutClick {
            override fun onLongClick(view : View, position: Int) {
                val builder = AlertDialog.Builder(this@BingActivity)
                builder.setTitle("删除消息")
                    .setMessage("删除的消息无法恢复。")
                    .setPositiveButton("确定") { _, _ ->
                        viewModel.deleteSelectedContent(contentDataList[position].id)
                    }
                    .setNegativeButton("取消") { _, _ ->
                    }
                builder.show()
            }

            override fun onClick(view: View, position: Int) {
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val data = contentDataList[position]
                val clip: ClipData = ClipData.newPlainText("text", data.content)
                clipboard.setPrimaryClip(clip)
                if (data.conversationId.isNotBlank()) {
                    viewModel.setConversationId(data.conversationId)
                    Toast.makeText(applicationContext, "已复制并设置上下文", Toast.LENGTH_SHORT).show()
                } else {
                    Toast.makeText(applicationContext, "已复制", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onDoubleClick(view: View, position: Int) {
                val intent = Intent(this@BingActivity, DetailActivity::class.java)
                intent.putExtra("id", contentDataList[position].id)
                startActivity(intent)
            }
        }
    }
}