import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import chardet
import threading

def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    return chardet.detect(raw_data)['encoding']

def get_total_size(file_list):
    return sum(os.path.getsize(file) for file in file_list)

def merge_sql_files(input_dir, output_file, progress_callback=None):
    sql_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.sql')]
    sql_files.sort()
    total_size = get_total_size(sql_files)
    processed_size = 0
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for file_path in sql_files:
            outfile.write(f"\n-- Beginn der Datei: {os.path.basename(file_path)}\n\n")
            
            file_encoding = detect_encoding(file_path)
            file_size = os.path.getsize(file_path)
            
            try:
                with open(file_path, 'r', encoding=file_encoding) as infile:
                    for line in infile:
                        outfile.write(line)
                        processed_size += len(line.encode(file_encoding))
                        if progress_callback:
                            progress_callback(processed_size, total_size)
            except UnicodeDecodeError:
                error_msg = f"-- Fehler: Konnte Datei {os.path.basename(file_path)} nicht lesen. Möglicherweise ungültige Kodierung.\n"
                outfile.write(error_msg)
                processed_size += file_size
                if progress_callback:
                    progress_callback(processed_size, total_size)
            
            outfile.write(f"\n\n-- Ende der Datei: {os.path.basename(file_path)}\n")
            outfile.write("-- " + "-" * 50 + "\n")

class SQLMergerGUI:
    def __init__(self, master):
        self.master = master
        master.title("SQL File Merger")
        master.geometry("400x300")

        self.input_dir = tk.StringVar()
        self.output_file = tk.StringVar()

        tk.Label(master, text="Input Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(master, textvariable=self.input_dir, width=30).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(master, text="Output File:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        tk.Entry(master, textvariable=self.output_file, width=30).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(master, text="Browse", command=self.browse_output).grid(row=1, column=2, padx=5, pady=5)

        self.merge_button = tk.Button(master, text="Merge SQL Files", command=self.start_merge)
        self.merge_button.grid(row=2, column=1, pady=20)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(master, variable=self.progress_var, maximum=100, length=300, mode='determinate')
        self.progress_bar.grid(row=3, column=0, columnspan=3, pady=10, padx=10, sticky="ew")

        self.progress_label = tk.Label(master, text="0%")
        self.progress_label.grid(row=4, column=1, pady=5)

    def browse_input(self):
        directory = filedialog.askdirectory()
        self.input_dir.set(directory)

    def browse_output(self):
        file = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL files", "*.sql")])
        self.output_file.set(file)

    def start_merge(self):
        input_dir = self.input_dir.get()
        output_file = self.output_file.get()

        if not input_dir or not output_file:
            messagebox.showerror("Error", "Please select both input directory and output file.")
            return

        self.merge_button.config(state='disabled')
        self.progress_var.set(0)
        self.progress_label['text'] = "0%"
        
        thread = threading.Thread(target=self.merge_files, args=(input_dir, output_file))
        thread.start()

    def merge_files(self, input_dir, output_file):
        try:
            merge_sql_files(input_dir, output_file, self.update_progress)
            self.master.after(0, self.show_success, output_file)
        except Exception as e:
            self.master.after(0, self.show_error, str(e))
        finally:
            self.master.after(0, self.reset_ui)

    def update_progress(self, processed_size, total_size):
        progress = (processed_size / total_size) * 100
        self.progress_var.set(progress)
        self.master.after(0, self.update_progress_label, progress)

    def update_progress_label(self, progress):
        self.progress_label['text'] = f"{progress:.1f}%"

    def show_success(self, output_file):
        messagebox.showinfo("Success", f"SQL files merged successfully. Output saved to {output_file}")

    def show_error(self, error_message):
        messagebox.showerror("Error", f"An error occurred: {error_message}")

    def reset_ui(self):
        self.merge_button.config(state='normal')
        self.progress_var.set(0)
        self.progress_label['text'] = "0%"

if __name__ == "__main__":
    root = tk.Tk()
    app = SQLMergerGUI(root)
    root.mainloop()