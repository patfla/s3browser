[app]
title = Codex1
package.name = codex1
package.domain = org.patfla
source.dir = .
source.include_exts = py
version = 0.3
requirements = python3,kivy,boto3,botocore,jmespath,idna,charset_normalizer,certifi,openssl,python-dateutil,s3transfer,plyer,pyjnius
# requirements = python3,kivy,boto3,python-dateutil,androidstorage4kivy @ https://github.com/kivy-garden/androidstorage4kivy/archive/master.zip
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
entrypoint = main.py
p4a.bootstrap = sdl2
android.private_storage = true
android.archs = arm64-v8a
android.ndk = 25b
# android.api = 33
android.api = 30
android.target_sdk_version = 30 
android.requestLegacyExternalStorage = True
android.minapi = 21
android.enable_splits = False
# debug = False  
# release = True
orientation = portrait

[android]
android.sdk_dir = ~/.buildozer/android/platform/android-sdk
android.ndk_dir = ~/.buildozer/android/platform/android-ndk-r25b
# REMOVED: android.api = 33 (this should be controlled by android.api in [app])
android.release = False # For debuggable builds and run-as
android.enable_audioservice = True
android.enable_multiprocess = True

# Remove or comment out these lines if they are present:
# android.no-byte-compile-python = 1
p4a.local_recipes = ./recipes

[buildozer]
# disable root warning for CI
warn_on_root = 0
