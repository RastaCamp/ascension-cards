package com.rastacamp.ascension

import android.webkit.WebView
import android.widget.Toast
import com.android.billingclient.api.AcknowledgePurchaseParams
import com.android.billingclient.api.BillingClient
import com.android.billingclient.api.BillingClientStateListener
import com.android.billingclient.api.BillingFlowParams
import com.android.billingclient.api.BillingResult
import com.android.billingclient.api.PendingPurchasesParams
import com.android.billingclient.api.ProductDetails
import com.android.billingclient.api.Purchase
import com.android.billingclient.api.PurchasesUpdatedListener
import com.android.billingclient.api.QueryProductDetailsParams
import com.android.billingclient.api.QueryPurchasesParams

class PlayBillingBridge(
    private val activity: MainActivity,
    private val webView: WebView,
) : PurchasesUpdatedListener {

    private var billingClient: BillingClient? = null
    private var ready = false
    private var productDetails: ProductDetails? = null

    fun start() {
        if (billingClient != null) return
        billingClient = BillingClient.newBuilder(activity)
            .setListener(this)
            .enablePendingPurchases(
                PendingPurchasesParams.newBuilder().enableOneTimeProducts().build(),
            )
            .build()
        billingClient?.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(result: BillingResult) {
                ready = result.responseCode == BillingClient.BillingResponseCode.OK
                if (ready) prefetchProduct()
            }

            override fun onBillingServiceDisconnected() {
                ready = false
            }
        })
    }

    private fun prefetchProduct() {
        val client = billingClient ?: return
        val params = QueryProductDetailsParams.newBuilder()
            .setProductList(
                listOf(
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(PRODUCT_ID)
                        .setProductType(BillingClient.ProductType.INAPP)
                        .build(),
                ),
            )
            .build()
        client.queryProductDetailsAsync(params) { result, list ->
            if (result.responseCode == BillingClient.BillingResponseCode.OK) {
                productDetails = list.firstOrNull()
            }
        }
    }

    fun purchasePro(productId: String) {
        activity.runOnUiThread {
            if (productId != PRODUCT_ID) {
                toast("Unknown product: $productId")
                return@runOnUiThread
            }
            val client = billingClient
            if (client == null || !ready) {
                toast("Google Play billing is not ready yet. Try again in a moment.")
                return@runOnUiThread
            }
            val details = productDetails
            if (details == null) {
                toast("Product not loaded from Play. Check Console product ID: $PRODUCT_ID")
                prefetchProduct()
                return@runOnUiThread
            }
            val offer = details.oneTimePurchaseOfferDetails
            if (offer == null) {
                toast("Purchase offer unavailable for $PRODUCT_ID")
                return@runOnUiThread
            }
            val productParams = BillingFlowParams.ProductDetailsParams.newBuilder()
                .setProductDetails(details)
                .build()
            val flowParams = BillingFlowParams.newBuilder()
                .setProductDetailsParamsList(listOf(productParams))
                .build()
            client.launchBillingFlow(activity, flowParams)
        }
    }

    fun restorePurchases() {
        activity.runOnUiThread {
            val client = billingClient
            if (client == null || !ready) {
                toast("Google Play billing is not ready yet.")
                return@runOnUiThread
            }
            client.queryPurchasesAsync(
                QueryPurchasesParams.newBuilder()
                    .setProductType(BillingClient.ProductType.INAPP)
                    .build(),
            ) { result, purchases ->
                if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                    toast("Could not check purchases (${result.debugMessage})")
                    return@queryPurchasesAsync
                }
                val owned = purchases.any {
                    it.products.contains(PRODUCT_ID) &&
                        it.purchaseState == Purchase.PurchaseState.PURCHASED
                }
                if (owned) {
                    purchases.filter { it.products.contains(PRODUCT_ID) }.forEach { handlePurchase(it) }
                    grantProToWeb()
                    toast("Master level restored.")
                } else {
                    toast("No purchase found for this Google Play account.")
                }
            }
        }
    }

    override fun onPurchasesUpdated(result: BillingResult, purchases: MutableList<Purchase>?) {
        if (result.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
            purchases.forEach { handlePurchase(it) }
            return
        }
        if (result.responseCode == BillingClient.BillingResponseCode.USER_CANCELED) return
        if (result.responseCode != BillingClient.BillingResponseCode.OK) {
            toast("Purchase failed (${result.debugMessage})")
        }
    }

    private fun handlePurchase(purchase: Purchase) {
        if (purchase.purchaseState != Purchase.PurchaseState.PURCHASED) return
        if (!purchase.products.contains(PRODUCT_ID)) return
        val client = billingClient ?: return
        if (!purchase.isAcknowledged) {
            val params = AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(purchase.purchaseToken)
                .build()
            client.acknowledgePurchase(params) { ack ->
                if (ack.responseCode == BillingClient.BillingResponseCode.OK) {
                    grantProToWeb()
                }
            }
        } else {
            grantProToWeb()
        }
    }

    private fun grantProToWeb() {
        webView.post {
            webView.evaluateJavascript(
                "(window.ascensionGrantProEntitlement&&ascensionGrantProEntitlement(true))",
                null,
            )
        }
    }

    private fun toast(msg: String) {
        Toast.makeText(activity, msg, Toast.LENGTH_LONG).show()
    }

    companion object {
        const val PRODUCT_ID = "ascension_pro_unlock"
    }
}
