package com.xmx.ai.detail.view
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import br.tiagohm.markdownview.css.styles.Github
import com.xmx.ai.databinding.ActivityDetailBinding
import com.xmx.ai.detail.viewModel.DetailViewModel
import java.util.regex.Pattern

class DetailActivity : AppCompatActivity() {

    private lateinit var binding : ActivityDetailBinding
    private val viewModel : DetailViewModel by viewModels()
    private var id : Long = -1
    var isActive : Boolean = false

    init {
        instance = this
    }
    companion object {
        var instance : DetailActivity? = null
    }

    override fun onCreate(savedInstanceState: Bundle?) {

        super.onCreate(savedInstanceState)

        binding = ActivityDetailBinding.inflate(layoutInflater)
        setContentView(binding.root)

        id = intent.getLongExtra("id", 0)
        loadContent(id)
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        if (intent != null) {
            id = intent.getLongExtra("id", 0)
            loadContent(id)
        }
    }

    fun loadContent(id : Long) {
        viewModel.initContentData(id)

        viewModel.content.observe(this) {
            if (it != null) {
                val entity = it
                val sb = StringBuilder(entity.content)
                if (entity.extra.isNotBlank()) {
                    try {
                        val regex = Regex("^\\[\\^\\w+\\^]:.*")
                        var index = 0
                        while (index < sb.length) {
                            val end = sb.indexOf("\n", index).let { if (it == -1) sb.length else it }
                            val line = sb.substring(index, end)
                            if (regex.matches(line)) {
                                sb.deleteRange(index, end + 1)
                            } else {
                                index = end + 1
                            }
                        }

                        var flag = false
                        val matcher = Pattern.compile("\\[\\^\\w+\\^]").matcher(entity.extra)
                        while (matcher.find()) {
                            val symbol = matcher.group(0)
                            if (symbol != null && !sb.contains(symbol)) {
                                if (!flag) {
                                    flag = true
                                    sb.append("\n")
                                }
                                sb.append(symbol)
                            }
                        }
                    }
                    catch (_: Exception) { }
                    sb.append("\n\n")
                    sb.append(entity.extra)
                }
                val css = Github()
                css.addRule("body",
                    "padding: 0px",
                    "padding-top: 20px",
                    "padding-left: 10px",
                    "padding-right: 10px",
                    "padding-bottom: 30px")
//                css.addFontFace("MyFont", "normal", "normal", "normal", "url('msyhmono.ttf')")
//                css.addRule(
//                    "p",
//                    "position: relative",
//                    "padding: 0px 0px",
//                    "border: 0",
//                    "border-radius: 3px",
//                    "background-color: #f6f8fa",
//                    "font-family: MyFont",
//                    "text-align: left",
//                    "font-size: 10px"
//                )
                binding.Content.addStyleSheet(css)
                val content = sb.toString()
                val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                val clip: ClipData = ClipData.newPlainText("text", content)
                clipboard.setPrimaryClip(clip)
                binding.Content.loadMarkdown(content)
            }
        }
    }

    override fun onResume() {
        super.onResume()
        isActive = true
    }

    override fun onPause() {
        super.onPause()
        isActive = false
    }
}