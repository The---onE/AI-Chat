package com.xmx.ai

import android.Manifest
import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.xmx.ai.bing.view.BingActivity
import com.xmx.ai.chatgpt.view.GptActivity
import timber.log.Timber

class App : Application() {
    // Context -> Global
    init {
        instance = this
    }
    companion object {

        private var instance : App? = null
        fun context() : Context {
            return instance!!.applicationContext
        }

        private const val channelId : String = "AIChat"

        fun createChannel() {
            // Create the NotificationChannel, but only on API 26+ because
            // the NotificationChannel class is new and not in the support library
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val name = "AIChat"
                val descriptionText = "AIChatNotification"
                val importance = NotificationManager.IMPORTANCE_HIGH
                val channel = NotificationChannel(channelId, name, importance).apply {
                    description = descriptionText
                }
                // Register the channel with the system
                val notificationManager: NotificationManager =
                    instance?.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                notificationManager.createNotificationChannel(channel)
            }
        }

        fun showNotify(type: Int, roomId: Long) {
//            if (ListActivity.instance != null && ListActivity.instance!!.isActive)
//                return
            if (type == 1 && BingActivity.instance != null && BingActivity.instance!!.isActive)
                return
            if (type == 2 && GptActivity.instance != null && GptActivity.instance!!.isActive)
                return

            if (NotificationManagerCompat.from(context()).areNotificationsEnabled()) {
                val intent = if (type == 1) Intent(context(), BingActivity::class.java) else Intent(context(), GptActivity::class.java)
                intent.putExtra("roomId", roomId)
                val content = if (type == 1) "收到NewBing回复" else "收到ChatGPT回复"

                val pendingIntent : PendingIntent = PendingIntent.getActivity(context(), 0, intent, PendingIntent.FLAG_MUTABLE or PendingIntent.FLAG_CANCEL_CURRENT)

                val builder = NotificationCompat.Builder(context(), channelId)
                    .setSmallIcon(R.drawable.gpt_img)
                    .setContentTitle("AIChatRoom")
                    .setContentText(content)
                    .setPriority(NotificationCompat.PRIORITY_HIGH)
                    .setContentIntent(pendingIntent)
                    .setAutoCancel(true)

                with(NotificationManagerCompat.from(context())) {
                    // notificationId is a unique int for each notification that you must define
                    if (ActivityCompat.checkSelfPermission(
                            context(),
                            Manifest.permission.POST_NOTIFICATIONS
                        ) != PackageManager.PERMISSION_GRANTED
                    ) {
                        Toast.makeText(context(), "需要开启通知权限", Toast.LENGTH_SHORT).show()
                        return
                    }
                    notify(1, builder.build())
                }
            }
        }
    }

    // Timber setting
    override fun onCreate() {
        super.onCreate()
        Timber.plant(Timber.DebugTree())
    }

}