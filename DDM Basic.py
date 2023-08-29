import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import requests
import cgi
import os
from urllib.parse import urlparse
import time


class DownloadManagerApp:
    def __init__(self, root):
        # Initialize variables
        self.root = root
        self.selected_folder = os.path.expanduser("~/Downloads")
        self.download_thread = None

        # Create UI elements
        self.root.title("Darq Download Manager")
        self.url_label = ttk.Label(root, text="Enter URL:")
        self.url_entry = ttk.Entry(root)
        self.folder_button = ttk.Button(root, text="Select Folder", command=self.select_folder)
        self.download_button = ttk.Button(root, text="Start Download", command=self.start_download)
        self.progress_bar = ttk.Progressbar(root, mode="determinate")
        self.footer_label = ttk.Label(root, text="Made with \u2764 by DarqPikachu.", anchor="w")

        # Place UI elements on grid
        self.footer_label.grid(row=2, columnspan=4, padx=10, pady=10, sticky="w")
        self.url_label.grid(row=0, column=0, padx=10, pady=10)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        self.folder_button.grid(row=0, column=2, padx=10, pady=10)
        self.download_button.grid(row=0, column=3, padx=10, pady=10)
        self.progress_bar.grid(row=1, columnspan=4, padx=10, pady=10, sticky="ew")

    def select_folder(self):
        self.selected_folder = filedialog.askdirectory()

    def start_download(self):
        url = self.url_entry.get()
        response = requests.get(url, stream=True)

        if not url:
            messagebox.showwarning("No URL Provided", "Please provide a URL.")
            return

        try:
            response.raise_for_status()  # Check if the response is successful

        except requests.exceptions.MissingSchema:
            messagebox.showerror("Invalid URL", "The provided URL is not valid.")
            return

        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Failed to connect to the server.\n Error: {e}")
            return

        if url and self.selected_folder:
            content_disposition = response.headers.get('content-disposition')  # Get filename from header
            if content_disposition:
                _, params = cgi.parse_header(content_disposition)
                filename = params.get('filename')
            else:
                filename = url.split("/")[-1] + ".html"  # Extract filename from URL

            total_size = int(response.headers.get("content-length", 0))
            domain = urlparse(url).netloc  # Extract the domain name

            # Display confirmation prompt
            confirmation_message = (f"You are downloading:\n"
                                    f"File: {filename}\n"
                                    f"Server: {domain}\n"
                                    f"Size: {total_size / (1024 * 1024):.2f} MB\n\n"
                                    f"Do you want to proceed?")

            confirmed = messagebox.askyesno("Confirm Download", confirmation_message)
            if confirmed:
                self.progress_bar["maximum"] = total_size
                start_time = time.time()  # Record start time
                self.download_thread = threading.Thread(target=self.download_file, args=(url, filename, start_time))
                self.download_thread.start()

    def download_file(self, url, filename, start_time):
        response = requests.get(url, stream=True)
        file_path = f"{self.selected_folder}/{filename}"
        downloaded_size = 0
        speed = 0
        elapsed_minutes = 0
        elapsed_seconds = 0
        last_update_time = time.time()  # Initialize the time counter

        with open(file_path, "wb") as file:
            for data in response.iter_content(chunk_size=1024):
                if not data:
                    break
                file.write(data)
                current_time = time.time()
                elapsed_time = current_time - start_time
                downloaded_size += len(data)

                if current_time - last_update_time >= 0.25:  # Check if quarter second has passed
                    last_update_time = current_time  # Update the time counter
                    self.progress_bar["value"] = downloaded_size
                    speed = downloaded_size / (1024 * 1024 * elapsed_time)  # MB/s
                    elapsed_minutes = elapsed_time // 60
                    elapsed_seconds = elapsed_time % 60
                    self.footer_label.config(text=f"Downloading Speed: {speed:.2f} MB/s   "
                                                  f"Elapsed Time: {elapsed_minutes:.0f}m {elapsed_seconds:.0f}s")
                    self.root.update_idletasks()

            self.progress_bar["value"] = 0
            self.footer_label.config(text="Made with \u2764 by DarqPikachu.")

        prompt_result = messagebox.askquestion("Download Completed.",
                                               f"The {filename} is downloaded."
                                               f"\nAverage Downloading Speed: {speed:.2f} MB/s"
                                               f"\nElapsed Time: {elapsed_minutes:.0f}m {elapsed_seconds:.0f}s"
                                               f"\nDo you want to open the folder?")

        if prompt_result == "yes":
            folder_path = os.path.dirname(file_path)
            os.startfile(folder_path)  # Open the folder in file explorer

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadManagerApp(root)
    app.run()
