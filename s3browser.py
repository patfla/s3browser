import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk
import boto3
import threading
import os

# === AWS Config ===
ACCESS_KEY = "abc"
SECRET_KEY = "xyz"
REGION_NAME = "us-east-1"

session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION_NAME,
)
s3 = session.client('s3')

# === App State ===
current_bucket = ""
current_prefix = ""
file_entries = []
sort_by = "name"
sort_reverse = False

# === GUI ===
ctk.set_default_color_theme("blue")
app = ctk.CTk()
app.title("S3 Browser")
app.geometry("900x600")

file_frame = ctk.CTkFrame(app)
file_frame.pack(fill='both', expand=True, padx=10, pady=10)

# Bucket dropdown
bucket_var = tk.StringVar()
bucket_dropdown = ttk.Combobox(file_frame, textvariable=bucket_var, state="readonly")
bucket_dropdown.pack(fill='x', padx=5, pady=5)
bucket_dropdown.bind("<<ComboboxSelected>>", lambda e: list_files())

def load_buckets():
    try:
        buckets = s3.list_buckets()['Buckets']
        names = [b['Name'] for b in buckets]
        bucket_dropdown['values'] = names
        if names:
            bucket_var.set(names[0])
            list_files()
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Filter row
filter_frame = ctk.CTkFrame(file_frame)
filter_frame.pack(fill='x', pady=5)

filter_label = ctk.CTkLabel(filter_frame, text="Name Filter:")
filter_label.pack(side='left', padx=(5, 2))

filter_entry = ctk.CTkEntry(filter_frame, width=200)
filter_entry.pack(side='left', padx=(2, 5))

def refresh_files():
    list_files()

refresh_btn = ctk.CTkButton(filter_frame, text="Apply Filter", command=refresh_files, width=100)
refresh_btn.pack(side='left', padx=5)

filter_entry.bind("<Tab>", lambda e: (refresh_btn.focus_set(), "break"))
refresh_btn.bind("<Return>", lambda e: refresh_files())

# Treeview with scrollbar
tree_frame = tk.Frame(file_frame)
tree_frame.pack(fill='both', expand=True)

tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
tree_scrollbar.pack(side="right", fill="y")

columns = ("name", "size")
file_tree = ttk.Treeview(
    tree_frame,
    columns=columns,
    show='headings',
    selectmode="extended",
    yscrollcommand=tree_scrollbar.set
)
file_tree.heading("name", text="Name")
file_tree.heading("size", text="Size")
file_tree.column("name", width=600, anchor="w")
file_tree.column("size", width=100, anchor="e")
file_tree.pack(fill='both', expand=True, side='left')

file_tree.bind("<Double-1>", lambda e: on_tree_double_click())
tree_scrollbar.config(command=file_tree.yview)

# Buttons for Upload, Download, Delete
button_frame = ctk.CTkFrame(file_frame)
button_frame.pack(pady=5)

def upload_files():
    file_paths = filedialog.askopenfilenames(title="Select files to upload")
    if not file_paths or not current_bucket:
        return

    def upload_thread():
        for path in file_paths:
            name = os.path.basename(path)
            key = current_prefix + name
            progress_bar.set(0)
            config = boto3.s3.transfer.TransferConfig(multipart_threshold=1024 * 25, max_concurrency=4)
            s3.upload_file(path, current_bucket, key, Callback=ProgressPercentage(path), Config=config)
        progress_bar.set(1)
        messagebox.showinfo("Done", f"Uploaded {len(file_paths)} file(s).")
        list_files()

    threading.Thread(target=upload_thread).start()

def download_files():
    selection = file_tree.selection()
    selected = [file_entries[file_tree.index(i)] for i in selection if file_entries[file_tree.index(i)]['type'] == 'file']
    if not selected:
        messagebox.showerror("Error", "Select one or more files.")
        return
    folder = filedialog.askdirectory(title="Choose download folder")
    if not folder:
        return

    def download_thread():
        for entry in selected:
            key = current_prefix + entry['name']
            path = os.path.join(folder, entry['name'])
            progress_bar.set(0)
            s3.download_file(current_bucket, key, path, Callback=ProgressPercentageDownload(key))
        progress_bar.set(1)
        messagebox.showinfo("Done", f"Downloaded {len(selected)} file(s).")

    threading.Thread(target=download_thread).start()

def delete_file():
    selection = file_tree.selection()
    if not selection or len(selection) != 1:
        messagebox.showerror("Error", "Select exactly one file to delete.")
        return
    idx = file_tree.index(selection[0])
    entry = file_entries[idx]
    if entry['type'] != 'file':
        messagebox.showerror("Error", "Can only delete files.")
        return
    key = current_prefix + entry['name']
    if not messagebox.askyesno("Confirm", f"Delete {entry['name']}?"):
        return
    s3.delete_object(Bucket=current_bucket, Key=key)
    messagebox.showinfo("Deleted", f"{entry['name']} deleted.")
    list_files()

upload_btn = ctk.CTkButton(button_frame, text="Upload Files", command=upload_files)
upload_btn.pack(side='left', padx=5)

download_btn = ctk.CTkButton(button_frame, text="Download Files", command=download_files)
download_btn.pack(side='left', padx=5)

delete_btn = ctk.CTkButton(button_frame, text="Delete File", command=delete_file)
delete_btn.pack(side='left', padx=5)

# Progress bar
progress_bar = ctk.CTkProgressBar(file_frame)
progress_bar.pack(pady=5, fill='x')

# Helpers
def format_size(size):
    if size is None:
        return ""
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def sort_tree(col):
    global sort_by, sort_reverse
    sort_reverse = (sort_by == col and not sort_reverse)
    sort_by = col
    list_files()

file_tree.heading("name", text="Name", command=lambda: sort_tree("name"))
file_tree.heading("size", text="Size", command=lambda: sort_tree("size"))

# Tree navigation handler
def on_tree_double_click():
    global current_prefix
    selection = file_tree.selection()
    if not selection:
        return
    idx = file_tree.index(selection[0])
    entry = file_entries[idx]
    print(f"Double-clicked entry: {entry}")

    if entry["type"] == "folder":
        current_prefix += entry["name"] + "/"
        list_files()
    elif entry["type"] == "up":
        current_prefix = "/".join(current_prefix.rstrip("/").split("/")[:-1])
        if current_prefix:
            current_prefix += "/"
        list_files()

# Main logic
def list_files():
    global current_bucket, current_prefix, file_entries
    bucket = bucket_var.get()
    if not bucket:
        return
    current_bucket = bucket
    filter_value = filter_entry.get().strip().lower()

    try:
        resp = s3.list_objects_v2(Bucket=bucket, Prefix=current_prefix, Delimiter="/")

        display_entries = []

        if current_prefix:
            display_entries.append({"type": "up", "name": "..", "size": None})

        if 'CommonPrefixes' in resp:
            for p in resp['CommonPrefixes']:
                name = p['Prefix'].replace(current_prefix, "").rstrip('/')
                if filter_value in name.lower():
                    display_entries.append({"type": "folder", "name": name, "size": None})

        if 'Contents' in resp:
            for obj in resp['Contents']:
                if obj['Key'] == current_prefix:
                    continue
                name = obj['Key'].replace(current_prefix, "")
                if '/' in name:
                    continue
                if filter_value in name.lower():
                    display_entries.append({"type": "file", "name": name, "size": obj['Size']})

        if sort_by == "name":
            display_entries.sort(key=lambda x: x['name'].lower(), reverse=sort_reverse)
        else:
            display_entries.sort(key=lambda x: x['size'] or 0, reverse=sort_reverse)

        file_tree.delete(*file_tree.get_children())
        file_entries.clear()

        for entry in display_entries:
            label = f"[Folder] {entry['name']}" if entry["type"] == "folder" else (
                "[ .. ]" if entry["type"] == "up" else entry["name"]
            )
            file_tree.insert('', 'end', values=(label, format_size(entry['size'])))
            file_entries.append(entry)

    except Exception as e:
        messagebox.showerror("Error", str(e))

# Progress Callbacks
class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        fraction = self._seen_so_far / self._size
        progress_bar.set(fraction)

class ProgressPercentageDownload(object):
    def __init__(self, key_name):
        self._seen_so_far = 0

    def __call__(self, bytes_amount):
        self._seen_so_far += bytes_amount
        progress_bar.step()

# Start
load_buckets()
app.mainloop()
