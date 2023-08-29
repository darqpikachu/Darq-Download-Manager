import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
import cgi
import os
from urllib.parse import urlparse
import time
import concurrent.futures
from tqdm import tqdm


class DownloadManagerApp:
    def __init__(self, root):
        # Initialize variables
        self.root = root
        self.selected_folder = os.path.expanduser("~/Downloads")
        self.download_thread = None
        self.last_filename = ""
        self.last_file_path = ""

        # Create UI elements
        self.root.title("Darq Download Manager")
        self.url_label = ttk.Label(root, text="Enter URL:")
        self.url_entry = ttk.Entry(root)
        self.folder_button = ttk.Button(root, text="Select Folder", command=self.select_folder)
        self.download_button = ttk.Button(root, text="Start Download", command=self.start_download)
        self.workers_label = ttk.Label(root, text="Number of Workers:")
        self.workers_scale = ttk.Scale(root, from_=1, to=128, orient="horizontal", value=8,
                                       command=self.update_workers_label)
        self.workers_value_label = ttk.Label(root, text="8")
        self.footer_label = ttk.Label(root, text="Made with \u2764 by DarqPikachu.", anchor="w")

        # Place UI elements on grid
        self.footer_label.grid(row=4, columnspan=4, padx=10, pady=10, sticky="w")
        self.url_label.grid(row=0, column=0, padx=10, pady=10)
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)
        self.folder_button.grid(row=0, column=2, padx=10, pady=10)
        self.download_button.grid(row=0, column=3, padx=10, pady=10)
        self.workers_label.grid(row=1, column=0, padx=10, pady=10)
        self.workers_scale.grid(row=1, column=1, columnspan=2, padx=10, pady=10)
        self.workers_value_label.grid(row=1, column=3, padx=10, pady=10)

    def update_workers_label(self, value):
        self.workers_value_label.config(text=round(float(value)))  # Update the label with current value

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
            num_workers = int(round(float(self.workers_scale.get())))  # Get the number of workers from the slider
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
                                    f"Maximum Workers: {num_workers}\n"
                                    f"Size: {total_size / (1024 * 1024):.2f} MB\n\n"
                                    f"Do you want to proceed?")

            confirmed = messagebox.askyesno("Confirm Download", confirmation_message)
            if confirmed:
                self.root.update_idletasks()  # Update the UI
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
                    self.download_thread = executor.submit(self.download_file, url, filename)
                self.check_download_progress()  # Start checking progress

    def download_file(self, url, filename):
        response = requests.get(url, stream=True)
        file_path = f"{self.selected_folder}/{filename}"
        total_size = int(response.headers.get("content-length", 0))
        with open(file_path, "wb") as file:
            with tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024) as progress_bar:
                for data in response.iter_content(chunk_size=1024):
                    if not data:
                        break
                    file.write(data)
                    progress_bar.update(len(data))  # Update the tqdm progress bar

        self.download_complete(file_path, filename)

    def download_complete(self, file_path, filename):
        self.last_filename = filename
        self.last_file_path = file_path

    def check_download_progress(self):
        while self.download_thread is not None and not self.download_thread.done():
            self.root.update_idletasks()  # Update the UI
            time.sleep(0.1)  # Wait for a short interval

        prompt_result = messagebox.askquestion("Download Completed.", f"The {self.last_filename} is downloaded."
                                                                      f"\nDo you want to open the folder?")
        if prompt_result == "yes":
            folder_path = os.path.dirname(self.last_file_path)
            os.startfile(folder_path)  # Open the folder in file explorer

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = DownloadManagerApp(root)
    app.run()
