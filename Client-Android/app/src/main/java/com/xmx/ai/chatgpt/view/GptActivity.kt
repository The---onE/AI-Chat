package com.xmx.ai.chatgpt.view

import android.Manifest
import android.app.Activity
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.OpenableColumns
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.ScrollView
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import coil.Coil
import coil.ImageLoader
import coil.decode.GifDecoder
import coil.decode.ImageDecoderDecoder
import coil.load
import com.xmx.ai.R
import com.xmx.ai.chatgpt.adapter.GptContentAdapter
import com.xmx.ai.chatgpt.viewModel.GptViewModel
import com.xmx.ai.database.entity.ContentEntity
import com.xmx.ai.databinding.ActivityGptBinding
import com.xmx.ai.detail.view.DetailActivity
import com.xmx.ai.list.view.ListActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.lang.Thread.sleep

class GptActivity : AppCompatActivity() {

    private lateinit var binding: ActivityGptBinding
    private val viewModel: GptViewModel by viewModels()
    private var contentDataList = ArrayList<ContentEntity>()
    private var roomId: Long = -1
    var isActive: Boolean = false

    init {
        instance = this
    }

    companion object {
        var instance: GptActivity? = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)

        roomId = intent.getLongExtra("roomId", 0)

        binding = ActivityGptBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val imageLoader = this.let {
            ImageLoader.Builder(it)
                .components {
                    if (Build.VERSION.SDK_INT >= 28) {
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

            if (contentDataList.size > 0) {
                val firstData = contentDataList[0]
                binding.EDViewSystem.setText(firstData.extra)
            } else {
                binding.EDViewSystem.setText("")
            }

            setContentListRV()
        }

        viewModel.deleteCheck.observe(this) {
            if (it == true) {
                viewModel.getContentData(roomId)
            }
        }

        viewModel.gptInsertCheck.observe(this) {
            if (it == true) {
                viewModel.getContentData(roomId)
                binding.loading.visibility = View.INVISIBLE
            }
        }

        viewModel.uploadFileCheck.observe(this) {
            if (!it.isNullOrBlank()) {
                Toast.makeText(applicationContext, it, Toast.LENGTH_SHORT).show()
            }
        }

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

        binding.uploadBtn.setOnClickListener {
            val text = binding.EDViewSystem.text
            if (text.startsWith("f:") && text.length > 2) {
                if (ContextCompat.checkSelfPermission(
                        this,
                        Manifest.permission.READ_EXTERNAL_STORAGE
                    ) != PackageManager.PERMISSION_GRANTED
                ) {
                    ActivityCompat.requestPermissions(
                        this,
                        arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE),
                        0
                    )
                } else {
                    openFile()
                }
            } else {
                Toast.makeText(
                    applicationContext,
                    "请在系统输入框输入\"f:【index】\"再上传",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }

        binding.EDView.onFocusChangeListener = View.OnFocusChangeListener { _, hasFocus ->
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as InputMethodManager
            if (hasFocus) {
                imm.showSoftInput(binding.EDView, InputMethodManager.SHOW_IMPLICIT)
            } else {
                imm.hideSoftInputFromWindow(binding.EDView.windowToken, 0)
            }
        }
    }


    private fun postRequest(isContext: Boolean) {
        val prevQuery = binding.EDView.text.toString()
        if (prevQuery.isNotBlank()) {
            binding.loading.visibility = View.VISIBLE

            var start = 2
            if (roomId <= 0) {
                roomId = System.currentTimeMillis()
                start = 1
            }

            viewModel.postResponse(
                prevQuery,
                isContext,
                binding.EDViewSystem.text.toString(),
                roomId,
                start
            )
            binding.EDView.setText("")
            sleep(100)
            viewModel.getContentData(roomId)
            binding.SVContainer.fullScroll(ScrollView.FOCUS_DOWN)
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
        } else {
            val intent = Intent(this, ListActivity::class.java)
            startActivity(intent)
        }
    }

    private fun setContentListRV() {
        val contentAdapter = GptContentAdapter(this, contentDataList)
        binding.RVContainer.adapter = contentAdapter
        binding.RVContainer.layoutManager = LinearLayoutManager(this).apply {
            stackFromEnd = true
        }

        if (contentDataList.size == 0)
            binding.uploadBtn.visibility = View.VISIBLE
        else
            binding.uploadBtn.visibility = View.GONE

        CoroutineScope(Dispatchers.Main).launch {
            delay(100)
            binding.SVContainer.fullScroll(ScrollView.FOCUS_DOWN)
        }

        contentAdapter.chatLayoutClick = object : GptContentAdapter.ChatLayoutClick {
            override fun onLongClick(view: View, position: Int) {

                val builder = AlertDialog.Builder(this@GptActivity)
                builder.setTitle("删除消息")
                    .setMessage("删除的消息无法恢复，请求的上下文中也会删除。")
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
                Toast.makeText(applicationContext, "已复制", Toast.LENGTH_SHORT).show()
            }

            override fun onDoubleClick(view: View, position: Int) {
                val intent = Intent(this@GptActivity, DetailActivity::class.java)
                intent.putExtra("id", contentDataList[position].id)
                startActivity(intent)
            }
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            0 -> {
                if ((grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED)) {
                    openFile()
                } else {
                    Toast.makeText(applicationContext, "授权失败", Toast.LENGTH_SHORT).show()
                }
                return
            }

            else -> {

            }
        }
    }

    private fun openFile() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
        }
        startActivityForResult(intent, 0)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == 0 && resultCode == Activity.RESULT_OK) {
            val uploadFileUri = data?.data!!
            if (binding.EDViewSystem.text.startsWith("f:")) {
                val index = binding.EDViewSystem.text.substring(2)
                CoroutineScope(Dispatchers.IO).launch {
                    sendPostRequest(uploadFileUri, index)
                }
            }
        }
    }

    private suspend fun sendPostRequest(fileUri: Uri?, index: String) {
        if (fileUri == null || index.isBlank())
            return

        try {
            val parcelFileDescriptor =
                contentResolver.openFileDescriptor(fileUri, "r", null) ?: return
            val inputStream = FileInputStream(parcelFileDescriptor.fileDescriptor)
            val cursor = contentResolver.query(fileUri, null, null, null, null)
            var name = ""
            cursor?.use {
                if (it.moveToFirst()) {
                    val id = it.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if (id >= 0) {
                        name = it.getString(id)
                    }
                }
            }
            val file = File(cacheDir, name)
            val outputStream = withContext(Dispatchers.IO) {
                FileOutputStream(file)
            }
            inputStream.copyTo(outputStream)
            viewModel.uploadFileResponse(file, index)
            parcelFileDescriptor.close()
        } catch (e: Exception) {
            Toast.makeText(applicationContext, e.toString(), Toast.LENGTH_SHORT).show()
        }
    }
}