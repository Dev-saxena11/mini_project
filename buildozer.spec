[app]

title = MyApp
package.name = myapp
package.domain = org.example

# Main entry
source.dir = .
source.main = main.py

# ... (other settings) ...


# Include all assets/templates/static
source.include_exts = py,kv,png,jpg,jpeg,html,css,js

# Version
version = 0.1

# Core requirements
requirements = python3,kivy,flask,flask-socketio,eventlet,jnius,itsdangerous,Jinja2,MarkupSafe,python-engineio,python-socketio,Werkzeug

# Permissions
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# API / SDK versions (sync with GitHub Actions)
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.build_tools_version = 33.0.2  # <-- Add this line

# Architectures
android.archs = arm64-v8a,armeabi-v7a

# Copy all libs (prevents missing modules at runtime)
android.copy_libs = 1

# Java class needed for WebView
android.java_classes = org.kivy.android.PythonActivity

# Orientation & fullscreen
orientation = portrait
fullscreen = 0
android.hide_statusbar = False

# Optional branding
presplash.filename = %(source.dir)s/data/presplash.png
icon.filename = %(source.dir)s/data/icon.png

# Backup allowed
android.allow_backup = True

# Release signing (disabled for debug builds)
android.release = False

