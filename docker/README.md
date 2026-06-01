# Docker

## Web app (default)

Serves `index.html`, `cards/`, and `audio/` on port **8765** (same as `Play-Ascension.bat`).

```powershell
cd path\to\ascension-cards
docker compose up --build
```

Open http://127.0.0.1:8765/

Stop:

```powershell
docker compose down
```

## Android debug build (optional)

Requires Unix `android/gradlew` (committed in repo). First-time image pull is large (~minutes).

```powershell
docker compose --profile android run --rm android-build
```

APK output: `android/app/build/outputs/apk/debug/app-debug.apk`
