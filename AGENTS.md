# AGENTS.md
## Setup
- Run `./setup.sh` to install Buildozer and the Android toolchain.
./setup.sh

## Setup
- Ensure Buildozer (and its dependencies such as python-for-android, Android SDK/NDK) are installed before the session’s network access is disabled.  
  *If these tools aren’t preinstalled or provided via a setup script, the build will fail.*

## Build
- Run `buildozer android debug` to generate an APK from `main.py` using `buildozer.spec`.

## Optional run
- If an emulator or device is available, run `buildozer android debug deploy run` to install and launch the app.