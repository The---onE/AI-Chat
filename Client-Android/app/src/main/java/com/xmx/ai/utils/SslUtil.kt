package com.xmx.ai.utils

import android.annotation.SuppressLint
import java.security.SecureRandom
import java.security.cert.CertificateException
import java.security.cert.X509Certificate
import javax.net.ssl.HostnameVerifier
import javax.net.ssl.SSLContext
import javax.net.ssl.SSLSession
import javax.net.ssl.SSLSocketFactory
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager

class SslUtil {
    companion object {
        @JvmStatic
        @SuppressLint("TrulyRandom")
        fun createSSLSocketFactory(): SSLSocketFactory? {
            var sslSocketFactory: SSLSocketFactory? = null
            try {
                val sc = SSLContext.getInstance("TLS")
                sc.init(
                    null, arrayOf<TrustManager>(TrustAllManager()),
                    SecureRandom()
                )
                sslSocketFactory = sc.socketFactory
            } catch (ignored: Exception) {
            }
            return sslSocketFactory
        }
    }

    class TrustAllManager : X509TrustManager {
        @SuppressLint("TrustAllX509TrustManager")
        @Throws(CertificateException::class)
        override fun checkClientTrusted(chain: Array<X509Certificate?>?, authType: String?) {
        }

        @SuppressLint("TrustAllX509TrustManager")
        @Throws(CertificateException::class)
        override fun checkServerTrusted(chain: Array<X509Certificate?>?, authType: String?) {
        }

        override fun getAcceptedIssuers(): Array<X509Certificate> {
            return emptyArray()
        }
    }

    class TrustAllHostnameVerifier : HostnameVerifier {
        @SuppressLint("BadHostnameVerifier")
        override fun verify(hostname: String, session: SSLSession): Boolean {
            return true
        }
    }
}