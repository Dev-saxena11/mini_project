[app]

# (str) Title of your application
title = MyApp

# (str) Package name
package.name = myapp

# (str) Package domain (unique ID, e.g. org.example.myapp)
package.domain = org.example

# (str) Source code where your main.py lives
source.dir = .

# (str) The main .py file
source.main = main.py

# (list) Include extensions
source.include_exts = py,kv,png,jpg,jpeg,html,css,js

# (str) Application versioning
version = 0.1

# (list) Application requirements
requirements = python3,kivy,flask,flask-socketio,eventlet,jnius,itsdangerous,Jinja2,MarkupSafe,python-engineio,python-socketio,Werkzeug

# (str) Entry point
entrypoint = main.py

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (bool) Indicate whether the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Ensure WebView works
android.java_classes = org.kivy.android.PythonActivity

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# Orientation
orientation = portrait

# (bool) Hide the statusbar
android.hide_statusbar = False

# (list) Presplash of the application
presplash.filename = %(source.dir)s/data/presplash.png

# Icon
icon.filename = %(source.dir)s/data/icon.png

# (str) Supported architectures
# 'armeabi-v7a','arm64-v8a','x86','x86_64'
android.archs = arm64-v8a,armeabi-v7a

# (bool) Sign the APK (needed for release)
android.release = False

# (bool) Enable backup
android.allow_backup = True
