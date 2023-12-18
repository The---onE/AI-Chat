package com.xmx.ai.utils

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class NetworkUtil {
    companion object{
        fun makeClient(baseUrl: String): Retrofit {
            val okHttpClient = OkHttpClient
                .Builder()
                .connectTimeout(5, TimeUnit.MINUTES)
                .readTimeout(5, TimeUnit.MINUTES)
                .writeTimeout(5, TimeUnit.MINUTES)
                .retryOnConnectionFailure(true)
                .hostnameVerifier(SslUtil.TrustAllHostnameVerifier())
                .sslSocketFactory(SslUtil.createSSLSocketFactory()!!, SslUtil.TrustAllManager())
                .build()

            return Retrofit
                .Builder()
                .baseUrl(baseUrl)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
    }
}