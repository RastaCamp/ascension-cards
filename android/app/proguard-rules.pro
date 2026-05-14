# Ascension — keep WebView JS bridge classes if you add @JavascriptInterface later
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
