package com.xmx.ai.list.adapter

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.constraintlayout.widget.ConstraintLayout
import androidx.recyclerview.widget.RecyclerView
import com.xmx.ai.R
import com.xmx.ai.database.entity.ContentEntity

class ListContentAdapter(val context : Context, private val dataSet : List<ContentEntity>) : RecyclerView.Adapter<ListContentAdapter.ViewHolder>() {

    interface ListLayoutClick {
        fun onLongClick(view : View, position: Int)
        fun onClick(view : View, position: Int)
    }
    var listLayoutClick : ListLayoutClick? = null

    inner class ViewHolder(view : View) : RecyclerView.ViewHolder(view) {
        val TVRoomType : TextView = view.findViewById(R.id.TVRoomType)
        val TVRoomStart : TextView = view.findViewById(R.id.TVRoomStart)
        val layout : ConstraintLayout = view.findViewById(R.id.listLayout)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.list_item, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.TVRoomType.text = if (dataSet[position].roomType == 1) "NewBing" else "ChatGPT"
        holder.TVRoomStart.text = dataSet[position].content

        holder.layout.setOnClickListener {view->
            listLayoutClick?.onClick(view, position)
        }

        holder.layout.setOnLongClickListener { view ->
            listLayoutClick?.onLongClick(view, position)
            return@setOnLongClickListener true
        }

    }

    override fun getItemCount(): Int {
        return dataSet.size
    }

}