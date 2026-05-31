import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from .cleaner import clean_duplicates, count_duplicate_numbers
from .exporter import export_records
from .models import MissedCallRecord
from .parser import extract_from_images


SUPPORTED_FILE_TYPES = [
    ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
    ("All files", "*.*"),
]


class CollapsibleSection(ctk.CTkFrame):
    def __init__(self, master, title: str, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.title = title
        self.is_open = True

        self.header = ctk.CTkButton(
            self,
            text=f"▼ {self.title}",
            command=self.toggle,
            anchor="w",
            height=34,
        )
        self.header.pack(fill="x", padx=8, pady=(8, 4))

        self.body = ctk.CTkFrame(self)
        self.body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def toggle(self):
        if self.is_open:
            self.body.pack_forget()
            self.header.configure(text=f"▶ {self.title}")
        else:
            self.body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            self.header.configure(text=f"▼ {self.title}")
        self.is_open = not self.is_open


class MissedCallsPhonLinkApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("MissedCallsPhonLink")
        self.geometry("1100x720")
        self.minsize(850, 560)

        self.selected_files = []
        self.records = []
        self.display_records = []
        self.is_processing = False

        self.output_format = tk.StringVar(value="xlsx")
        self.auto_clean = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Ready. Upload Phone Link missed-call screenshots.")

        self._build_layout()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self)
        container.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        container.grid_columnconfigure(0, weight=0, minsize=330)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(container, width=340)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        right = ctk.CTkFrame(container)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(0, weight=1)

        self._build_upload_section(left)
        self._build_action_section(left)
        self._build_duplicate_section(left)
        self._build_status_section(left)
        self._build_preview_section(right)

    def _build_upload_section(self, parent):
        section = CollapsibleSection(parent, "File Upload Section")
        section.pack(fill="x", padx=4, pady=4)

        self.file_count_label = ctk.CTkLabel(section.body, text="No files selected", anchor="w")
        self.file_count_label.pack(fill="x", padx=8, pady=(8, 4))

        self.file_listbox = tk.Listbox(section.body, height=8)
        self.file_listbox.pack(fill="both", expand=True, padx=8, pady=4)

        ctk.CTkButton(section.body, text="Upload File", command=self.upload_files).pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(section.body, text="Clear Selected Files", command=self.clear_files).pack(fill="x", padx=8, pady=(4, 8))

    def _build_action_section(self, parent):
        section = CollapsibleSection(parent, "Action Section")
        section.pack(fill="x", padx=4, pady=4)

        ctk.CTkButton(section.body, text="Preview Button", command=self.preview_data).pack(fill="x", padx=8, pady=(8, 4))
        ctk.CTkButton(section.body, text="Extract Data", command=self.extract_data).pack(fill="x", padx=8, pady=4)

        ctk.CTkLabel(section.body, text="Output format:", anchor="w").pack(fill="x", padx=8, pady=(12, 2))
        ctk.CTkRadioButton(section.body, text="XLSX", variable=self.output_format, value="xlsx").pack(anchor="w", padx=8, pady=2)
        ctk.CTkRadioButton(section.body, text="CSV", variable=self.output_format, value="csv").pack(anchor="w", padx=8, pady=(2, 8))

    def _build_duplicate_section(self, parent):
        section = CollapsibleSection(parent, "Duplicate Cleaner")
        section.pack(fill="x", padx=4, pady=4)

        self.duplicate_summary_label = ctk.CTkLabel(section.body, text="No data yet", anchor="w", justify="left")
        self.duplicate_summary_label.pack(fill="x", padx=8, pady=(8, 4))

        ctk.CTkCheckBox(
            section.body,
            text="Auto-clean duplicates before export",
            variable=self.auto_clean,
        ).pack(anchor="w", padx=8, pady=4)

        ctk.CTkButton(section.body, text="Clean Duplicates", command=self.clean_duplicates_in_preview).pack(
            fill="x", padx=8, pady=(4, 8)
        )

    def _build_status_section(self, parent):
        section = CollapsibleSection(parent, "Status / Log Section")
        section.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(section.body, textvariable=self.status_text, wraplength=300, justify="left", anchor="w").pack(
            fill="x", padx=8, pady=8
        )

    def _build_preview_section(self, parent):
        section = CollapsibleSection(parent, "Preview Section")
        section.pack(fill="both", expand=True, padx=4, pady=4)
        section.body.grid_columnconfigure(0, weight=1)
        section.body.grid_rowconfigure(0, weight=1)

        columns = ("PhoneNumber", "Missed Call Date", "Missed Call Time")
        self.tree = ttk.Treeview(section.body, columns=columns, show="headings")
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=180, anchor="center")

        y_scroll = ttk.Scrollbar(section.body, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(section.body, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def upload_files(self):
        files = filedialog.askopenfilenames(title="Select Phone Link screenshots", filetypes=SUPPORTED_FILE_TYPES)
        if not files:
            return
        for file_path in files:
            if file_path not in self.selected_files:
                self.selected_files.append(file_path)
        self._refresh_file_list()
        self._set_status(f"Selected {len(self.selected_files)} file(s).")

    def clear_files(self):
        self.selected_files.clear()
        self.records.clear()
        self.display_records.clear()
        self._refresh_file_list()
        self._refresh_table([])
        self._update_duplicate_summary([])
        self._set_status("Cleared selected files and preview data.")

    def preview_data(self):
        if self.is_processing:
            return
        if not self.selected_files:
            messagebox.showwarning("No files", "Please upload one or more screenshots first.")
            return
        self._run_in_thread(self._preview_worker)

    def extract_data(self):
        if self.is_processing:
            return
        if not self.display_records:
            messagebox.showwarning("No data", "Please preview data before extracting.")
            return

        try:
            records_to_export = self.display_records
            if self.auto_clean.get():
                records_to_export = clean_duplicates(records_to_export)
                self.display_records = records_to_export
                self._refresh_table(records_to_export)
                self._update_duplicate_summary(records_to_export)

            output_path = export_records(records_to_export, self.output_format.get())
            self._set_status(f"Export complete: {output_path}")
            messagebox.showinfo("Export complete", f"File saved:\n{output_path}")
        except Exception as exc:
            self._set_status(f"Export failed: {exc}")
            messagebox.showerror("Export failed", str(exc))

    def clean_duplicates_in_preview(self):
        if not self.display_records:
            messagebox.showwarning("No data", "Please preview data first.")
            return
        before = len(self.display_records)
        self.display_records = clean_duplicates(self.display_records)
        after = len(self.display_records)
        self._refresh_table(self.display_records)
        self._update_duplicate_summary(self.display_records)
        self._set_status(f"Duplicate cleaning completed. Rows: {before} -> {after}")

    def _preview_worker(self):
        try:
            self._set_processing(True, "OCR processing started. Please wait...")
            records = extract_from_images(self.selected_files)
            records = sorted(records, key=lambda item: item.missed_at, reverse=True)
            self.records = records
            self.display_records = records
            self.after(0, lambda: self._refresh_table(records))
            self.after(0, lambda: self._update_duplicate_summary(records))
            self._set_status(f"Preview generated. Extracted {len(records)} row(s).")
        except Exception as exc:
            self._set_status(f"Preview failed: {exc}")
            self.after(0, lambda: messagebox.showerror("Preview failed", str(exc)))
        finally:
            self._set_processing(False)

    def _run_in_thread(self, target):
        thread = threading.Thread(target=target, daemon=True)
        thread.start()

    def _set_processing(self, processing: bool, message: str = None):
        self.is_processing = processing
        if message:
            self._set_status(message)

    def _set_status(self, message: str):
        self.after(0, lambda: self.status_text.set(message))

    def _refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        for file_path in self.selected_files:
            self.file_listbox.insert(tk.END, Path(file_path).name)
        self.file_count_label.configure(text=f"Selected files: {len(self.selected_files)}")

    def _refresh_table(self, records):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for record in records:
            self.tree.insert(
                "",
                tk.END,
                values=(record.phone_number, record.missed_call_date, record.missed_call_time),
            )

    def _update_duplicate_summary(self, records):
        raw_count = len(records)
        duplicate_numbers = count_duplicate_numbers(records)
        unique_count = len({record.phone_number for record in records})
        self.duplicate_summary_label.configure(
            text=(
                f"Rows in preview: {raw_count}\n"
                f"Duplicate numbers found: {duplicate_numbers}\n"
                f"Unique numbers: {unique_count}"
            )
        )
