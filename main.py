import os
import threading
import boto3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.progressbar import ProgressBar
from kivy.uix.popup import Popup
from kivy.clock import Clock

# Attempt to import Android storage helpers
try:
    from android.storage import primary_external_storage_path
except Exception:
    primary_external_storage_path = lambda: os.getcwd()

try:
    from plyer import filechooser
except Exception:
    filechooser = None
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION_NAME = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")


session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION_NAME,
)
s3 = session.client("s3")

# === Helpers ===
def format_size(size):
    if size is None:
        return ""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


class ProgressPercentage:
    def __init__(self, filename, app):
        self.app = app
        self._size = float(os.path.getsize(filename))
        self._seen = 0

    def __call__(self, bytes_amount):
        self._seen += bytes_amount
        fraction = self._seen / self._size
        Clock.schedule_once(lambda dt: self.app.update_progress(fraction))

class ProgressPercentageDownload:
    def __init__(self, total_bytes, app):
        self.app = app
        self.total = float(total_bytes)
        self.seen = 0

    def __call__(self, bytes_amount):
        self.seen += bytes_amount
        fraction = self.seen / self.total
        Clock.schedule_once(lambda dt: self.app.update_progress(fraction))

class FileRow(BoxLayout):
    def __init__(self, entry, index, app, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=40, **kwargs)
        self.entry = entry
        self.index = index
        self.app = app
        if entry["type"] == "file":
            self.btn = ToggleButton(text=entry["name"], halign="left", size_hint_x=0.7)
            self.btn.bind(on_release=self.on_toggle)
            self.add_widget(self.btn)
            self.add_widget(Label(text=format_size(entry["size"]), size_hint_x=0.3))
        else:
            label = "[Folder] " + entry["name"] if entry["type"] == "folder" else "[ .. ]"
            self.btn = Button(text=label, halign="left", size_hint_x=0.7)
            self.btn.bind(on_release=self.on_click)
            self.add_widget(self.btn)
            self.add_widget(Label(text="", size_hint_x=0.3))

    def on_click(self, instance):
        self.app.open_entry(self.entry)

    def on_toggle(self, instance):
        self.app.toggle_selection(self.index, instance.state == "down")


class codex1App(App):
    def build(self):
        self.current_bucket = ""
        self.current_prefix = ""
        self.file_entries = []
        self.selected = set()
        self.sort_by = "name"
        self.sort_reverse = False

        root = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.bucket_spinner = Spinner(text="Loading buckets...", size_hint_y=None, height=50)
        self.bucket_spinner.bind(text=lambda spinner, text: self.list_files())
        root.add_widget(self.bucket_spinner)

        filter_row = BoxLayout(size_hint_y=None, height=40, spacing=5)
        self.filter_input = TextInput(hint_text="Name filter")
        filter_row.add_widget(self.filter_input)
        apply_btn = Button(text="Apply")
        apply_btn.bind(on_release=lambda x: self.list_files())
        filter_row.add_widget(apply_btn)
        root.add_widget(filter_row)

        self.scroll = ScrollView()
        self.file_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.file_layout.bind(minimum_height=self.file_layout.setter("height"))
        self.scroll.add_widget(self.file_layout)
        root.add_widget(self.scroll)

        btn_row = BoxLayout(size_hint_y=None, height=60, spacing=5)
        upload_btn = Button(text="Upload")
        upload_btn.bind(on_release=lambda x: self.upload_files())
        btn_row.add_widget(upload_btn)
        download_btn = Button(text="Download")
        download_btn.bind(on_release=lambda x: self.download_files())
        btn_row.add_widget(download_btn)
        delete_btn = Button(text="Delete")
        delete_btn.bind(on_release=lambda x: self.delete_file())
        btn_row.add_widget(delete_btn)
        root.add_widget(btn_row)

        self.progress = ProgressBar(max=1.0, value=0.0, size_hint_y=None, height=20)
        root.add_widget(self.progress)

        Clock.schedule_once(lambda dt: self.load_buckets())
        return root

    def show_error(self, msg):
        popup = Popup(title="Error", content=Label(text=msg), size_hint=(0.8, 0.4))
        popup.open()

    def update_progress(self, fraction):
        self.progress.value = fraction

    # === AWS Interaction ===
    def load_buckets(self):
        try:
            buckets = s3.list_buckets()["Buckets"]
            names = [b["Name"] for b in buckets]
            self.bucket_spinner.values = names
            if names:
                self.bucket_spinner.text = names[0]
                self.list_files()
            else:
                self.bucket_spinner.text = "No buckets"
        except Exception as e:
            self.show_error(str(e))

    def list_files(self):
        bucket = self.bucket_spinner.text
        if not bucket:
            return
        self.current_bucket = bucket
        filter_value = self.filter_input.text.strip().lower()
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=self.current_prefix, Delimiter="/")
            display_entries = []
            if self.current_prefix:
                display_entries.append({"type": "up", "name": "..", "size": None})
            if "CommonPrefixes" in resp:
                for p in resp["CommonPrefixes"]:
                    name = p["Prefix"].replace(self.current_prefix, "").rstrip("/")
                    if filter_value in name.lower():
                        display_entries.append({"type": "folder", "name": name, "size": None})
            if "Contents" in resp:
                for obj in resp["Contents"]:
                    if obj["Key"] == self.current_prefix:
                        continue
                    name = obj["Key"].replace(self.current_prefix, "")
                    if "/" in name:
                        continue
                    if filter_value in name.lower():
                        display_entries.append({"type": "file", "name": name, "size": obj["Size"]})
            if self.sort_by == "name":
                display_entries.sort(key=lambda x: x["name"].lower(), reverse=self.sort_reverse)
            else:
                display_entries.sort(key=lambda x: x["size"] or 0, reverse=self.sort_reverse)
            self.file_entries = display_entries
            self.selected.clear()
            self.refresh_view()
        except Exception as e:
            self.show_error(str(e))

    def refresh_view(self):
        self.file_layout.clear_widgets()
        for idx, entry in enumerate(self.file_entries):
            self.file_layout.add_widget(FileRow(entry, idx, self))

    def open_entry(self, entry):
        if entry["type"] == "folder":
            self.current_prefix += entry["name"] + "/"
            self.list_files()
        elif entry["type"] == "up":
            self.current_prefix = "/".join(self.current_prefix.rstrip("/").split("/")[:-1])
            if self.current_prefix:
                self.current_prefix += "/"
            self.list_files()

    def toggle_selection(self, index, selected):
        if selected:
            self.selected.add(index)
        else:
            self.selected.discard(index)

    def upload_files(self):
        if not self.current_bucket:
            self.show_error("Select a bucket first")
            return
        if filechooser:
            filechooser.open_file(multiple=True, on_selection=self._upload_selected)
        else:
            self.show_error("File chooser not available")

    def _upload_selected(self, paths):
        if not paths:
            return
        def upload_thread():
            for path in paths:
                name = os.path.basename(path)
                key = self.current_prefix + name
                config = boto3.s3.transfer.TransferConfig(multipart_threshold=1024*25, max_concurrency=4)
                s3.upload_file(path, self.current_bucket, key, Callback=ProgressPercentage(path,self), Config=config)
            Clock.schedule_once(lambda dt: self.after_upload(len(paths)))
        threading.Thread(target=upload_thread).start()

    def after_upload(self, count):
        self.progress.value = 0
        self.show_error(f"Uploaded {count} file(s)")
        self.list_files()

    def download_files(self):
        selected = [self.file_entries[i] for i in self.selected if self.file_entries[i]["type"] == "file"]
        if not selected:
            self.show_error("Select one or more files")
            return
        if filechooser and hasattr(filechooser, "choose_dir"):
            filechooser.choose_dir(on_selection=lambda paths: self._download_to(paths, selected))
        else:
            self._download_to([primary_external_storage_path()], selected)

    def _download_to(self, paths, selected):
        if not paths:
            return
        folder = paths[0]
        def download_thread():
            for entry in selected:
                key = self.current_prefix + entry["name"]
                path = os.path.join(folder, entry["name"])
                s3.download_file(self.current_bucket, key, path,
                                 Callback=ProgressPercentageDownload(entry[¨size¨],self))
                Clock.schedule_once(lambda dt: self.after_download(len(selected)))
        threading.Thread(target=download_thread).start()
    # def _download_to(self, paths, selected):
    #     if not paths:
    #         return
    #     folder = paths[0]
    #     def download_thread():
    #         for entry in selected:
    #             key = self.current_prefix + entry["name"]
    #             path = os.path.join(folder, entry["name"])
    #             s3.download_file(self.current_bucket, key, path, Callback=ProgressPercentageDownload(self))
    #         Clock.schedule_once(lambda dt: self.after_download(len(selected)))
    #     threading.Thread(target=download_thread).start()

    def after_download(self, count):
        self.progress.value = 0
        self.show_error(f"Downloaded {count} file(s)")

    def delete_file(self):
        if len(self.selected) != 1:
            self.show_error("Select exactly one file to delete")
            return
        idx = list(self.selected)[0]
        entry = self.file_entries[idx]
        if entry["type"] != "file":
            self.show_error("Can only delete files")
            return
        def confirm(instance):
            popup.dismiss()
            key = self.current_prefix + entry["name"]
            s3.delete_object(Bucket=self.current_bucket, Key=key)
            self.show_error(f"Deleted {entry['name']}")
            self.list_files()
        popup = Popup(title="Confirm", content=Button(text=f"Delete {entry['name']}?"), size_hint=(0.8,0.4))
        popup.content.bind(on_release=confirm)
        popup.open()

if __name__ == "__main__":
    codex1App().run()
