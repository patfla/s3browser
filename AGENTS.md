# AGENTS.md
## Setup
- Run the following script to install Buildozer, python-for-android, and the Android SDK/NDK:
  ```sh
  bash install_android_tools.sh
  ```
- Ensure Buildozer (and its dependencies such as python-for-android, Android SDK/NDK) are installed before the session’s network access is disabled.
  *If these tools aren’t preinstalled or provided via a setup script, the build will fail.*

## Build
- Run `buildozer android debug` to generate an APK from `main.py` using `buildozer.spec`.
  ```sh
  source buildozer-env/bin/activate
  buildozer android debug
  ```

## Optional run
- If an emulator or device is available, run `buildozer android debug deploy run` to install and launch the app.
