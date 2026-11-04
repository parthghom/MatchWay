# MatchWay app (React Native, Android Studio)

No Expo. Open the `android/` folder in Android Studio and press Run.

## One-time setup
1. Install Node 22+, JDK 17+, Android Studio (with an emulator or a phone with USB debugging).
2. `cd matchway-app && npm install`
3. Edit `src/config.js`: set `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
4. In Supabase > Authentication > URL Configuration > Redirect URLs, add `matchway://auth-callback`.

## Run
1. Backend: `cd matchway-backend && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000`
2. Metro: `cd matchway-app && npm start`
3. Android Studio: open `matchway-app/android`, press Run (or `npm run android`).
   The emulator reaches your PC's backend at `10.0.2.2:8000`, so no IP is needed.

## Backend URL for friends
Deploy `matchway-backend` (Render / Railway), then put its https URL in `HOSTED_API` in `src/config.js`.

## Build an APK to share
`cd matchway-app/android && ./gradlew assembleRelease`
Output: `android/app/build/outputs/apk/release/app-release.apk`
