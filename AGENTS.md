# AGENTS.md

## Setup
- Ensure Buildozer (and its dependencies such as python-for-android, Android SDK/NDK) are installed before the session’s network access is disabled.
  *If these tools aren’t preinstalled or provided via a setup script, the build will fail.*
- Run the following commands to install Buildozer and its dependencies:
  ```sh
  chmod u+x setup.sh
  ./setup.sh
  ```

## Build
- Run `buildozer android debug` to generate an APK from `main.py` using `buildozer.spec`.

## Optional run
- If an emulator or device is available, run `buildozer android debug deploy run` to install and launch the app.
