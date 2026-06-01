package com.rastacamp.ascension

import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.widget.Toast
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInAccount
import com.google.android.gms.auth.api.signin.GoogleSignInClient
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException

class GoogleAuthBridge(
    private val activity: AppCompatActivity,
    private val webView: WebView,
) {
    private val signInClient: GoogleSignInClient
    private lateinit var signInLauncher: ActivityResultLauncher<android.content.Intent>

    init {
        val options = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestEmail()
            .build()
        signInClient = GoogleSignIn.getClient(activity, options)
    }

    fun registerLauncher() {
        signInLauncher = activity.registerForActivityResult(
            ActivityResultContracts.StartActivityForResult(),
        ) { result ->
            val task = GoogleSignIn.getSignedInAccountFromIntent(result.data)
            try {
                val account = task.getResult(ApiException::class.java)
                onSignedIn(account)
            } catch (e: ApiException) {
                Toast.makeText(activity, "Sign-in cancelled or failed.", Toast.LENGTH_SHORT).show()
            }
        }
        val last = GoogleSignIn.getLastSignedInAccount(activity)
        if (last != null) onSignedIn(last)
    }

    @JavascriptInterface
    fun signIn() {
        activity.runOnUiThread {
            signInLauncher.launch(signInClient.signInIntent)
        }
    }

    @JavascriptInterface
    fun signOut() {
        activity.runOnUiThread {
            signInClient.signOut().addOnCompleteListener {
                pushAccountToWeb(null)
            }
        }
    }

    private fun onSignedIn(account: GoogleSignInAccount) {
        val email = account.email ?: account.displayName ?: "Google account"
        pushAccountToWeb(email)
        Toast.makeText(activity, "Signed in as $email", Toast.LENGTH_SHORT).show()
    }

    private fun pushAccountToWeb(email: String?) {
        val js = if (email.isNullOrBlank()) {
            "(window.ascensionOnGoogleAccount&&ascensionOnGoogleAccount(null))"
        } else {
            "(window.ascensionOnGoogleAccount&&ascensionOnGoogleAccount(${org.json.JSONObject.quote(email)}))"
        }
        webView.post { webView.evaluateJavascript(js, null) }
    }
}
