package com.xmx.ai.bing.adapter

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.constraintlayout.widget.ConstraintLayout
import androidx.recyclerview.widget.RecyclerView
import com.xmx.ai.R
import com.xmx.ai.database.entity.ContentEntity


class BingContentAdapter(val context : Context, private val dataSet : List<ContentEntity>) : RecyclerView.Adapter<BingContentAdapter.ViewHolder>() {

    companion object {
        private const val Ai = 1
        private const val User = 2
    }

    interface ChatLayoutClick {
        fun onLongClick(view : View, position: Int)
        fun onClick(view : View, position: Int)
        fun onDoubleClick(view : View, position: Int)
    }
    var chatLayoutClick : ChatLayoutClick? = null
    var lastClickTime : Long = 0

    inner class ViewHolder(view : View) : RecyclerView.ViewHolder(view) {
        val contentTV : TextView = view.findViewById(R.id.rvItemTV)
        val delChatLayout : ConstraintLayout = view.findViewById(R.id.chatLayout)
        val idHolder : TextView = view.findViewById(R.id.holdingId)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        return if (viewType == Ai) {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.ai_content_item, parent, false)
            ViewHolder(view)
        } else {
            val view = LayoutInflater.from(parent.context).inflate(R.layout.user_content_item, parent, false)
            ViewHolder(view)
        }
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.contentTV.text = dataSet[position].content
        holder.idHolder.text = dataSet[position].id.toString()

        holder.delChatLayout.setOnClickListener {view->
            if (System.currentTimeMillis() - lastClickTime > 1000) {
                lastClickTime = System.currentTimeMillis()
                chatLayoutClick?.onClick(view, position)
            }else {
                chatLayoutClick?.onDoubleClick(view, position)
            }
        }

        holder.delChatLayout.setOnLongClickListener { view ->
            chatLayoutClick?.onLongClick(view, position)
            return@setOnLongClickListener true
        }

    }

    override fun getItemCount(): Int {
        return dataSet.size
    }

    override fun getItemViewType(position: Int): Int {
        return if (dataSet[position].ai == 1) {
            Ai
        } else {
            User
        }
    }

}