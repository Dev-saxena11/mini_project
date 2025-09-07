[app]

# (str) Title of your application
title = Your Flask App

# (str) Package name
package.name = myflaskapp

# (str) Package domain (needed for android/ios packaging)
package.domain = com.rudrasingh

# (str) Source code where the main.py live
source.dir = .

# (str) Main python file to run
source.main_py = main.py

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (str) Application versioning (method 1)
# Increased to 0.2 to avoid conflicts
version = 0.2

# (list) Application requirements
# ADDED flask, which was the critical missing piece
requirements = python3,kivy,flask

# (list) Supported orientations
orientation = portrait

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android version code
# ADDED the version code, increased to 2
android.versioncode = 2

# (str) Android NDK version to use
android.ndk = 25c

# (int) Android NDK API to use. This is the minimum API your app will support, it should usually match android.minapi.
android.ndk_api = 21

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then automatically accept SDK license agreements
android.accept_sdk_license = True

# (list) The Android archs to build for
# ADDED armeabi-v7a for better compatibility
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1