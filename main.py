# In main.py

import threading
import traceback
import webbrowser
from kivy.app import App
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.clock import Clock

# Import the run_server function from your app.py
from app import run_server

class ClientApp(App):
    def build(self):
        # Start your Flask server in a background thread on all platforms
        print("Starting Flask server thread...")
        server_thread = threading.Thread(target=run_server)
        server_thread.daemon = True
        server_thread.start()

        if platform == 'android':
            # --- This code will only run on Android devices ---
            try:
                from jnius import autoclass
                WebView = autoclass('android.webkit.WebView')
                WebViewClient = autoclass('android.webkit.WebViewClient')
                Activity = autoclass('org.kivy.android.PythonActivity')

                activity = Activity.mActivity
                webview = WebView(activity)
                webview.setWebViewClient(WebViewClient())
                webview.getSettings().setJavaScriptEnabled(True)
                activity.setContentView(webview)
                
                # Give the server a moment to start before loading the URL
                Clock.schedule_once(lambda dt: webview.loadUrl('http://127.0.0.1:5000/'), 2)

                # Return a placeholder Kivy widget
                return Label()

            except Exception as e:
                # If anything goes wrong on Android, display the error
                error_message = traceback.format_exc()
                return Label(text=error_message)
        else:
            # --- This code will run on Windows, macOS, or Linux ---
            print("Desktop platform detected. Opening web browser.")
            # Give the server a moment to start, then open the browser
            Clock.schedule_once(lambda dt: webbrowser.open('http://127.0.0.1:5000/'), 2)
            
            # Display a helpful message in the Kivy window
            return Label(text='Server is running.\nYour web browser has been opened.')

if __name__ == '__main__':
    ClientApp().run()