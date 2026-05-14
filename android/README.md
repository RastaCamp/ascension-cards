# Ascension — Android wrapper (Google Play)

The store does **not** accept a raw `index.html`. You ship an **Android App Bundle (`.aab`)** built from this folder. The app is a **WebView** that loads your bundled site from assets (copied from the repo root on each build).

## Prerequisites

- [Android Studio](https://developer.android.com/studio) (includes Android SDK + JDK)
- Same machine: repo layout `ascension-cards/index.html` next to `ascension-cards/android/`

## Open & build

1. **File → Open** → select the **`android`** folder (not the repo root).
2. Wait for Gradle sync. If prompted, accept SDK licenses / install platforms.
3. **Build → Generate Signed App Bundle or APK** → **Android App Bundle** → create or choose a **upload key** (Play App Signing will manage the final key).
4. Upload the generated **`.aab`** to Play Console.

### Test on a phone from PowerShell (USB debugging on)

This folder includes **`gradlew.bat`** + the Gradle wrapper. Expo Go / Metro do **not** run this app; you install the **debug APK** or an **APK set from an `.aab`** like any native Android build.

**Quick install (debug APK — same idea as `adb install` after a native debug build):**

```powershell
cd path\to\ascension-cards\android
.\Build-InstallDebug.ps1
```

**Test a real `.aab` shape (debug-signed) with bundletool + adb:**

```powershell
.\Build-InstallBundleDebug.ps1
```

First run downloads **bundletool** into `android/tools/`. Release Play uploads still use **`bundleRelease`** + your signing config.

**Manual equivalents:**

```powershell
$env:JAVA_HOME = "${env:ProgramFiles}\Android\Android Studio\jbr"
$env:ANDROID_HOME = "${env:LOCALAPPDATA}\Android\Sdk"
.\gradlew.bat assembleDebug
& "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe" install -r .\app\build\outputs\apk\debug\app-debug.apk
```

```powershell
.\gradlew.bat bundleDebug
# → app\build\outputs\bundle\debug\app-debug.aab
```

**Release bundle for Play** (upload key — never commit secrets):

1. Copy `keystore.properties.example` → `keystore.properties` in this folder.
2. Create an upload keystore in this folder (example):

   ```powershell
   keytool -genkeypair -v -keystore ascension-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias ascension
   ```

3. Set `storeFile`, passwords, and `keyAlias` in `keystore.properties` to match.

```powershell
.\Build-ReleaseBundle.ps1
# or: .\gradlew.bat bundleRelease
# → app\build\outputs\bundle\release\app-release.aab
```

## Package name & version

- `applicationId`: **`com.rastacamp.ascension`** (`app/build.gradle`)
- Bump **`versionCode`** / **`versionName`** for each Play upload.

Change the id only if you create a **new** Play listing (it must match the app you create in the console).

## Web assets

The **`syncWebAssets`** Gradle task copies before each build:

- `../index.html`
- `../cards/`
- `../audio/`

into generated assets. Edit the web app in the parent folder, then rebuild the bundle.

## Play Billing (Pro IAP)

This scaffold **does not** include Billing Library code. You still need to:

1. Add Google Play Billing dependency and `BillingClient` flow for product id **`ascension_pro_unlock`**.
2. After a verified purchase or restore, call JS:  
   `ascensionGrantProEntitlement(true)`  
   (e.g. `WebView.evaluateJavascript`).

Optional: implement `window.AscensionPlayBilling.purchasePro` / `restorePurchases` via `@JavascriptInterface`.

## Icons

The launcher icon is the bundled card back (`res/drawable-nodpi/ic_launcher_card_back.png`). Regenerate from `cards/back.png` after asset changes if needed.
