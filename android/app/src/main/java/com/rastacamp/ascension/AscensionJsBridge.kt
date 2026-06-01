package com.rastacamp.ascension

import android.webkit.JavascriptInterface
import android.webkit.WebView

/**
 * Exposed to WebView as window.AscensionPlayBilling and window.AscensionGoogleAuth.
 */
class AscensionJsBridge(
    private val billing: PlayBillingBridge,
    private val google: GoogleAuthBridge,
) {
    @JavascriptInterface
    fun purchasePro(productId: String) {
        billing.purchasePro(productId)
    }

    @JavascriptInterface
    fun restorePurchases() {
        billing.restorePurchases()
    }

    @JavascriptInterface
    fun signIn() {
        google.signIn()
    }

    @JavascriptInterface
    fun signOut() {
        google.signOut()
    }
}

fun WebView.attachAscensionBridges(billing: PlayBillingBridge, google: GoogleAuthBridge) {
    val bridge = AscensionJsBridge(billing, google)
    addJavascriptInterface(object {
        @JavascriptInterface fun purchasePro(productId: String) = bridge.purchasePro(productId)
        @JavascriptInterface fun restorePurchases() = bridge.restorePurchases()
    }, "AscensionPlayBilling")
    addJavascriptInterface(object {
        @JavascriptInterface fun signIn() = bridge.signIn()
        @JavascriptInterface fun signOut() = bridge.signOut()
    }, "AscensionGoogleAuth")
}
