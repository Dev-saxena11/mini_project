# In buildozer.spec

[app]
title = Your Flask App
package.name = myflaskapp
package.domain = com.rudrasingh
source.dir = .
source.main_py = main.py

requirements = python3,kivy,flask,flask_socketio,jnius
source.include_patterns = app.py,database.py,templates/*,static/*

version = 1.0
orientation = portrait

[android]
android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.versioncode = 1
android.private_storage = True
android.accept_sdk_license = True

[buildozer]
log_level = 2