# main.py

# Imports for debugging, Flask, threading, and Kivy
import traceback
import threading
import time
from flask import Flask
from kivy.app import App
from kivy.uix.label import Label
from kivy.utils import platform

# --- 1. THE SERVER (Your Flask App) ---
# This part of the code creates the website.
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    # This is the HTML content your app will show.
    return "<h1>Success!</h1><p>Your Flask server is running inside the Kivy app.</p>"

# We need a function that we can run in a background thread.
def run_flask_app():
    flask_app.run(host='127.0.0.1', port=5000)


# --- 2. THE CLIENT (Your Kivy App for Android) ---
# This part of the code displays the website on Android.
class WebApp(App):
    def build(self):
        # This try/except block will display any errors on the screen instead of crashing.
        try:
            # Start the Flask server in a separate thread.
            # The 'daemon=True' part means the thread will close when the app closes.
            server_thread = threading.Thread(target=run_flask_app)
            server_thread.daemon = True
            server_thread.start()
            # Give the server a moment to start up before trying to load the URL.
            time.sleep(2)

            # Now, we create the WebView to display the server's content.
            # This code will only run on Android.
            from jnius import autoclass
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            Activity = autoclass('org.kivy.android.PythonActivity')

            activity = Activity.mActivity
            webview = WebView(activity)
            webview.setWebViewClient(WebViewClient())
            webview.getSettings().setJavaScriptEnabled(True)
            activity.setContentView(webview)

            # The URL must be 'http://127.0.0.1:5000' because the server
            # is now running ON THE PHONE itself (also known as 'localhost').
            webview.loadUrl('http://127.0.0.1:5000')

            # We must return a Kivy widget, but it won't be visible behind the WebView.
            # This is just to keep Kivy's build process happy.
            return Label(text="Loading WebView...")

        except Exception as e:
            # If anything goes wrong, display the full error on the screen.
            error_message = traceback.format_exc()
            return Label(text=error_message)


# --- 3. MAIN EXECUTION ---
if __name__ == '__main__':
    # For the APK, we only care about the 'android' platform.
    if platform == 'android':
        WebApp().run()
    else:
        # This allows you to test the server on your desktop.
        print("Flask server running for desktop testing. Open http://127.0.0.1:5000 in your browser.")
        run_flask_app()