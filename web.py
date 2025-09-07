import webview
from kivy.app import App
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.core.window import Window

# --- Android WebView (Pyjnius) - With improved error handling ---
try:
    # These imports will only succeed on an actual Android device
    from jnius import autoclass, JavaException
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    Activity = autoclass('org.kivy.android.PythonActivity')
# Catch the error if jnius isn't installed OR if it can't find the Android classes
except (ImportError, JavaException):
    # On desktop, these variables will be None
    WebView = None


# This Kivy App class will ONLY be used on Android
class WebApp(App):
    def build(self):
        self.url = 'http://10.0.2.2:5000' # For Android emulator, this IP points to the host machine
        
        # This check is redundant now but good for safety
        if platform == 'android' and WebView:
            self.activity = Activity.mActivity
            self.webview = WebView(self.activity)
            self.webview.setWebViewClient(WebViewClient())
            self.webview.getSettings().setJavaScriptEnabled(True)
            Window.bind(on_resize=self.on_window_resize)
            self.activity.setContentView(self.webview)
            self.webview.loadUrl(self.url)
            return Label(text="Android WebView is active.") # Kivy needs a widget returned
        
        # Fallback for safety, though this part of the code shouldn't be reached on desktop.
        return Label(text="This platform is not supported.")

    def on_window_resize(self, window, width, height):
        if platform == 'android' and hasattr(self, 'webview'):
            self.webview.layout(0, 0, width, height)


# --- Main Execution Block ---
if __name__ == '__main__':
    # This is the new logic: decide which app to run based on the platform.
    if platform in ('win', 'linux', 'macosx'):
        # --- On Desktop, run pywebview directly ---
        url = 'http://127.0.0.1:5000' # Use localhost for desktop
        webview.create_window('Your Flask App', url)
        webview.start() # This is a blocking call that runs on the main thread
    
    elif platform == 'android':
        # --- On Android, run the Kivy App ---
        WebApp().run() # This is a blocking call that runs on the main thread