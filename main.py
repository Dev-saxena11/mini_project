# In main.py

import threading
import traceback
# Add this comment to trigger the build
from kivy.app import App
from kivy.uix.label import Label

# Import the run_server function from your app.py
from app import run_server

class ClientApp(App):
    def build(self):
        try:
            # Start your full Flask server in a background thread
            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()

            # Create the WebView to display the server's content
            from jnius import autoclass
            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            Activity = autoclass('org.kivy.android.PythonActivity')

            activity = Activity.mActivity
            webview = WebView(activity)
            webview.setWebViewClient(WebViewClient())
            webview.getSettings().setJavaScriptEnabled(True)
            webview.getSettings().setAllowFileAccess(True) # Important for templates
            activity.setContentView(webview)
            
            # Load the root URL of your Flask app after a short delay
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: webview.loadUrl('http://127.0.0.1:5000/'), 3)

            return Label() # Return a placeholder widget

        except Exception as e:
            # If anything goes wrong, display the full error on the screen
            error_message = traceback.format_exc()
            return Label(text=error_message)

if __name__ == '__main__':
    if platform == 'android':
        ClientApp().run()
    else:
        run_server()
