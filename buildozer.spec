# In buildozer.spec

[app]
title = Travel Together
package.name = myflaskapp
package.domain = com.rudrasingh
source.dir = .
source.main_py = main.py

requirements = python3,kivy,flask,flask_socketio,jnius,blinker,click,colorama,gunicorn,itsdangerous,Jinja2,MarkupSafe,python-engineio,python-socketio,simple-websocket,Werkzeug
source.include_patterns = app.py,database.py,travel_together.db,templates/*,static/*

version = 1.0
orientation = portrait

[android]
android.permissions = INTERNET
android.api = 34
android.build_tools_version = 34.0.0

android.archs = arm64-v8a, armeabi-v7a
android.minapi = 21
android.versioncode = 1
android.private_storage = True
android.accept_sdk_license = True

[buildozer]
log_level = 2