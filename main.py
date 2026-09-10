import os
import sys
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from config_manager import load_config, save_config
from downloader_engine import DownloaderEngine, check_ffmpeg
from cloud_syncer import CloudSyncer

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class UltimateMediaCloudSyncer(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config_data = load_config()
        ctk.set_appearance_mode(self.config_data.get("theme_mode", "Dark"))
        ctk.set_default_color_theme(self.config_data.get("accent_theme", "blue"))

        self.title("Ultimate Media Cloud Syncer Pro")
        self.geometry("980x760")
        self.minsize(880, 680)

        self.current_engine = None
        self.current_syncer = None
        self.is_processing = False
        self.queue_items = []

        self._build_ui()
        self._load_config_into_ui()
        self._check_ffmpeg_status()

    def _build_ui(self):
        # Top Header Bar
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.pack(fill="x", padx=15, pady=(15, 5))

        self.logo_label = ctk.CTkLabel(
            self.header_frame, 
            text="🚀 Ultimate Media Cloud Syncer Pro", 
            font=("Arial", 22, "bold")
        )
        self.logo_label.pack(side="left", padx=20, pady=12)

        self.theme_switch = ctk.CTkSwitch(
            self.header_frame, 
            text="Dark Mode", 
            command=self._toggle_theme
        )
        self.theme_switch.pack(side="right", padx=20, pady=12)
        if self.config_data.get("theme_mode") == "Dark":
            self.theme_switch.select()
        else:
            self.theme_switch.deselect()

        self.ffmpeg_badge = ctk.CTkLabel(
            self.header_frame, 
            text="FFmpeg: Checking...", 
            font=("Arial", 11, "bold"),
            text_color="gray"
        )
        self.ffmpeg_badge.pack(side="right", padx=15)

        # Tabview Main Navigation
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_downloader = self.tabview.add("📥 Downloader & Syncer")
        self.tab_batch = self.tabview.add("📋 Batch Queue")
        self.tab_cloud = self.tabview.add("☁️ Cloud Credentials")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self._build_downloader_tab()
        self._build_batch_tab()
        self._build_cloud_tab()
        self._build_settings_tab()

    # ---------------- TAB 1: DOWNLOADER ----------------
    def _build_downloader_tab(self):
        # URL Input Section
        self.url_frame = ctk.CTkFrame(self.tab_downloader, fg_color="transparent")
        self.url_frame.pack(fill="x", padx=10, pady=(5, 5))

        self.url_lbl = ctk.CTkLabel(self.url_frame, text="Media URL / Playlist / Channel Link:", font=("Arial", 13, "bold"))
        self.url_lbl.pack(anchor="w", padx=5, pady=(0, 2))

        self.url_input_box = ctk.CTkFrame(self.url_frame, fg_color="transparent")
        self.url_input_box.pack(fill="x")

        self.url_input = ctk.CTkEntry(
            self.url_input_box, 
            placeholder_text="Paste YouTube, TikTok, SoundCloud, or Direct Media URL...", 
            font=("Arial", 13)
        )
        self.url_input.pack(side="left", fill="x", expand=True, padx=(5, 5))

        self.paste_btn = ctk.CTkButton(self.url_input_box, text="📋 Paste", width=80, command=self._paste_clipboard)
        self.paste_btn.pack(side="left", padx=2)

        self.clear_url_btn = ctk.CTkButton(self.url_input_box, text="❌ Clear", width=80, fg_color="transparent", border_width=1, command=lambda: self.url_input.delete(0, "end"))
        self.clear_url_btn.pack(side="left", padx=2)

        # Options Frame Grid
        self.options_grid = ctk.CTkFrame(self.tab_downloader, corner_radius=8)
        self.options_grid.pack(fill="x", padx=10, pady=5)

        # Download Format Preset
        self.fmt_lbl = ctk.CTkLabel(self.options_grid, text="Asset Download Workflow:", font=("Arial", 12, "bold"))
        self.fmt_lbl.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 2))

        self.format_var = ctk.StringVar(value=self.config_data.get("default_format", "Video Only"))
        self.format_selector = ctk.CTkSegmentedButton(
            self.options_grid,
            values=["Video Only", "Audio Only", "Transcript Only", "Everything Combo"],
            variable=self.format_var,
            command=self._on_format_changed
        )
        self.format_selector.grid(row=1, column=0, columnspan=4, sticky="ew", padx=15, pady=(0, 10))

        # Resolution, Audio Codec, Subtitle Language & Format Dropdowns
        self.res_lbl = ctk.CTkLabel(self.options_grid, text="Video Quality:")
        self.res_lbl.grid(row=2, column=0, sticky="w", padx=15, pady=2)
        self.res_var = ctk.StringVar(value=self.config_data.get("default_resolution", "Best Quality"))
        self.res_dropdown = ctk.CTkOptionMenu(self.options_grid, values=["Best Quality", "1080p Full HD", "720p HD", "480p"], variable=self.res_var)
        self.res_dropdown.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))

        self.audio_lbl = ctk.CTkLabel(self.options_grid, text="Audio Format:")
        self.audio_lbl.grid(row=2, column=1, sticky="w", padx=15, pady=2)
        self.audio_var = ctk.StringVar(value=self.config_data.get("default_audio_codec", "mp3"))
        self.audio_dropdown = ctk.CTkOptionMenu(self.options_grid, values=["mp3", "m4a", "wav", "flac"], variable=self.audio_var)
        self.audio_dropdown.grid(row=3, column=1, sticky="ew", padx=15, pady=(0, 10))

        self.sublang_lbl = ctk.CTkLabel(self.options_grid, text="Subtitle Lang:")
        self.sublang_lbl.grid(row=2, column=2, sticky="w", padx=15, pady=2)
        self.sublang_var = ctk.StringVar(value=self.config_data.get("default_subtitle_lang", "en"))
        self.sublang_dropdown = ctk.CTkOptionMenu(self.options_grid, values=["en", "es", "fr", "de", "zh", "all"], variable=self.sublang_var)
        self.sublang_dropdown.grid(row=3, column=2, sticky="ew", padx=15, pady=(0, 10))

        self.subfmt_lbl = ctk.CTkLabel(self.options_grid, text="Subtitle Format:")
        self.subfmt_lbl.grid(row=2, column=3, sticky="w", padx=15, pady=2)
        self.subfmt_var = ctk.StringVar(value=self.config_data.get("default_subtitle_format", "srt"))
        self.subfmt_dropdown = ctk.CTkOptionMenu(self.options_grid, values=["srt", "vtt", "txt"], variable=self.subfmt_var)
        self.subfmt_dropdown.grid(row=3, column=3, sticky="ew", padx=15, pady=(0, 10))

        self.options_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Destination & Directory Row
        self.dest_frame = ctk.CTkFrame(self.tab_downloader, corner_radius=8)
        self.dest_frame.pack(fill="x", padx=10, pady=5)

        self.dest_lbl = ctk.CTkLabel(self.dest_frame, text="Target Sync Destination:", font=("Arial", 12, "bold"))
        self.dest_lbl.pack(anchor="w", padx=15, pady=(8, 2))

        self.dest_var = ctk.StringVar(value="Local Disk")
        self.dest_selector = ctk.CTkSegmentedButton(
            self.dest_frame,
            values=["Local Disk", "MEGA.nz", "Telegram", "Local + Cloud"],
            variable=self.dest_var
        )
        self.dest_selector.pack(fill="x", padx=15, pady=(0, 8))

        self.dir_input_box = ctk.CTkFrame(self.dest_frame, fg_color="transparent")
        self.dir_input_box.pack(fill="x", padx=15, pady=(0, 10))

        self.dir_lbl = ctk.CTkLabel(self.dir_input_box, text="Save Folder:")
        self.dir_lbl.pack(side="left", padx=(0, 10))

        self.dir_entry = ctk.CTkEntry(self.dir_input_box, font=("Arial", 12))
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.dir_entry.insert(0, self.config_data.get("download_dir", ""))

        self.browse_btn = ctk.CTkButton(self.dir_input_box, text="📁 Browse", width=90, command=self._browse_download_dir)
        self.browse_btn.pack(side="left")

        # Delete local cache checkbox
        self.delete_cache_var = tk.BooleanVar(value=self.config_data.get("delete_local_after_upload", False))
        self.delete_cache_chk = ctk.CTkCheckBox(
            self.dest_frame,
            text="Delete temporary cache files after successful cloud upload",
            variable=self.delete_cache_var
        )
        self.delete_cache_chk.pack(anchor="w", padx=15, pady=(0, 10))

        # Progress Metrics Card
        self.metrics_frame = ctk.CTkFrame(self.tab_downloader, corner_radius=8)
        self.metrics_frame.pack(fill="x", padx=10, pady=5)

        self.status_lbl = ctk.CTkLabel(self.metrics_frame, text="Status: Ready", font=("Arial", 13, "bold"))
        self.status_lbl.pack(anchor="w", padx=15, pady=(8, 2))

        self.file_progress_lbl = ctk.CTkLabel(self.metrics_frame, text="Current Download: Idle", font=("Arial", 11), text_color="gray")
        self.file_progress_lbl.pack(anchor="w", padx=15, pady=(0, 2))

        self.file_progress_bar = ctk.CTkProgressBar(self.metrics_frame, height=12)
        self.file_progress_bar.set(0)
        self.file_progress_bar.pack(fill="x", padx=15, pady=(0, 10))

        # Action & Control Buttons
        self.ctrl_frame = ctk.CTkFrame(self.tab_downloader, fg_color="transparent")
        self.ctrl_frame.pack(fill="x", padx=10, pady=5)

        self.action_btn = ctk.CTkButton(
            self.ctrl_frame, 
            text="🚀 Execute Download & Sync Pipeline", 
            font=("Arial", 15, "bold"),
            height=42,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.start_pipeline
        )
        self.action_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.cancel_btn = ctk.CTkButton(
            self.ctrl_frame, 
            text="🛑 Cancel", 
            font=("Arial", 14, "bold"),
            height=42,
            width=120,
            fg_color="#c0392b",
            hover_color="#962d22",
            state="disabled",
            command=self.cancel_pipeline
        )
        self.cancel_btn.pack(side="right", padx=(5, 0))

        # Monitor Console Log Window
        self.log_header = ctk.CTkFrame(self.tab_downloader, fg_color="transparent")
        self.log_header.pack(fill="x", padx=10, pady=(5, 0))

        self.log_lbl = ctk.CTkLabel(self.log_header, text="Real-Time Terminal Console:", font=("Arial", 12, "bold"))
        self.log_lbl.pack(side="left", padx=5)

        self.copy_log_btn = ctk.CTkButton(self.log_header, text="📋 Copy Log", width=90, height=24, command=self._copy_log)
        self.copy_log_btn.pack(side="right", padx=2)

        self.clear_log_btn = ctk.CTkButton(self.log_header, text="🧹 Clear Log", width=90, height=24, fg_color="transparent", border_width=1, command=self._clear_log)
        self.clear_log_btn.pack(side="right", padx=2)

        self.open_folder_btn = ctk.CTkButton(self.log_header, text="📂 Open Folder", width=100, height=24, command=self._open_output_folder)
        self.open_folder_btn.pack(side="right", padx=2)

        self.monitor_log = ctk.CTkTextbox(self.tab_downloader, font=("Courier", 12), height=140)
        self.monitor_log.pack(fill="both", expand=True, padx=10, pady=(5, 10))

    # ---------------- TAB 2: BATCH QUEUE ----------------
    def _build_batch_tab(self):
        self.batch_info_lbl = ctk.CTkLabel(
            self.tab_batch, 
            text="Batch Processing Queue - Paste multiple URLs below (one URL per line):", 
            font=("Arial", 13, "bold")
        )
        self.batch_info_lbl.pack(anchor="w", padx=15, pady=(15, 5))

        self.batch_text = ctk.CTkTextbox(self.tab_batch, font=("Arial", 12), height=180)
        self.batch_text.pack(fill="x", padx=15, pady=5)
        self.batch_text.insert("1.0", "# Paste links here (e.g. YouTube videos, playlists, TikToks)\n")

        self.batch_btn_frame = ctk.CTkFrame(self.tab_batch, fg_color="transparent")
        self.batch_btn_frame.pack(fill="x", padx=15, pady=10)

        self.add_queue_btn = ctk.CTkButton(
            self.batch_btn_frame, 
            text="➕ Load Links to Downloader", 
            font=("Arial", 13, "bold"),
            command=self._load_batch_links
        )
        self.add_queue_btn.pack(side="left", padx=(0, 10))

        self.clear_batch_btn = ctk.CTkButton(
            self.batch_btn_frame, 
            text="🧹 Clear Input", 
            fg_color="transparent", 
            border_width=1,
            command=lambda: self.batch_text.delete("1.0", "end")
        )
        self.clear_batch_btn.pack(side="left")

    # ---------------- TAB 3: CLOUD CREDENTIALS ----------------
    def _build_cloud_tab(self):
        # MEGA Card
        self.mega_card = ctk.CTkFrame(self.tab_cloud, corner_radius=10)
        self.mega_card.pack(fill="x", padx=15, pady=10)

        self.mega_title = ctk.CTkLabel(self.mega_card, text="🔴 MEGA.nz Account Credentials", font=("Arial", 14, "bold"))
        self.mega_title.pack(anchor="w", padx=15, pady=(12, 5))

        self.mega_email_entry = ctk.CTkEntry(self.mega_card, placeholder_text="MEGA Email Address", width=400)
        self.mega_email_entry.pack(anchor="w", padx=15, pady=5)
        self.mega_email_entry.insert(0, self.config_data.get("mega_email", ""))

        self.mega_pass_entry = ctk.CTkEntry(self.mega_card, placeholder_text="MEGA Account Password", show="*", width=400)
        self.mega_pass_entry.pack(anchor="w", padx=15, pady=5)
        self.mega_pass_entry.insert(0, self.config_data.get("mega_password", ""))

        self.test_mega_btn = ctk.CTkButton(self.mega_card, text="🔌 Test MEGA Connection", command=self._test_mega_connection)
        self.test_mega_btn.pack(anchor="w", padx=15, pady=(5, 15))

        # Telegram Card
        self.tg_card = ctk.CTkFrame(self.tab_cloud, corner_radius=10)
        self.tg_card.pack(fill="x", padx=15, pady=10)

        self.tg_title = ctk.CTkLabel(self.tg_card, text="✈️ Telegram Cloud Setup", font=("Arial", 14, "bold"))
        self.tg_title.pack(anchor="w", padx=15, pady=(12, 5))

        self.tg_bot_entry = ctk.CTkEntry(self.tg_card, placeholder_text="Telegram Bot Token (Recommended - e.g. 123456:ABC...)", width=500)
        self.tg_bot_entry.pack(anchor="w", padx=15, pady=5)
        self.tg_bot_entry.insert(0, self.config_data.get("telegram_bot_token", ""))

        self.tg_chat_entry = ctk.CTkEntry(self.tg_card, placeholder_text="Target Chat ID or Channel ID (e.g. 123456789 or @channel)", width=500)
        self.tg_chat_entry.pack(anchor="w", padx=15, pady=5)
        self.tg_chat_entry.insert(0, self.config_data.get("telegram_chat_id", ""))

        self.tg_api_id_entry = ctk.CTkEntry(self.tg_card, placeholder_text="Optional User API ID (for Pyrogram)", width=300)
        self.tg_api_id_entry.pack(anchor="w", padx=15, pady=5)
        self.tg_api_id_entry.insert(0, self.config_data.get("telegram_api_id", ""))

        self.tg_api_hash_entry = ctk.CTkEntry(self.tg_card, placeholder_text="Optional User API Hash", width=300)
        self.tg_api_hash_entry.pack(anchor="w", padx=15, pady=5)
        self.tg_api_hash_entry.insert(0, self.config_data.get("telegram_api_hash", ""))

        self.test_tg_btn = ctk.CTkButton(self.tg_card, text="🔌 Test Telegram Connection", command=self._test_telegram_connection)
        self.test_tg_btn.pack(anchor="w", padx=15, pady=(5, 15))

        # Save Credentials Button
        self.save_cred_btn = ctk.CTkButton(
            self.tab_cloud, 
            text="💾 Save Cloud Credentials", 
            font=("Arial", 13, "bold"),
            height=35,
            command=self._save_cloud_credentials
        )
        self.save_cred_btn.pack(anchor="w", padx=15, pady=10)

    # ---------------- TAB 4: SETTINGS ----------------
    def _build_settings_tab(self):
        self.settings_card = ctk.CTkFrame(self.tab_settings, corner_radius=10)
        self.settings_card.pack(fill="both", expand=True, padx=15, pady=15)

        self.stg_title = ctk.CTkLabel(self.settings_card, text="Global Preferences & Metadata", font=("Arial", 15, "bold"))
        self.stg_title.pack(anchor="w", padx=15, pady=(15, 10))

        # Metadata options
        self.write_thumb_var = tk.BooleanVar(value=self.config_data.get("write_thumbnail", True))
        self.write_thumb_chk = ctk.CTkCheckBox(self.settings_card, text="Download and write video thumbnail image", variable=self.write_thumb_var)
        self.write_thumb_chk.pack(anchor="w", padx=15, pady=5)

        self.write_json_var = tk.BooleanVar(value=self.config_data.get("write_info_json", False))
        self.write_json_chk = ctk.CTkCheckBox(self.settings_card, text="Save video info metadata JSON file", variable=self.write_json_var)
        self.write_json_chk.pack(anchor="w", padx=15, pady=5)

        self.save_settings_btn = ctk.CTkButton(
            self.settings_card, 
            text="💾 Save All Settings", 
            font=("Arial", 14, "bold"),
            height=38,
            command=self._save_global_settings
        )
        self.save_settings_btn.pack(anchor="w", padx=15, pady=20)

    # ---------------- LOGIC & THREAD-SAFE UI METHODS ----------------
    def log(self, text):
        def _append():
            self.monitor_log.insert("end", f"[*] {text}\n")
            self.monitor_log.see("end")
        self.after(0, _append)

    def update_progress_ui(self, progress_data):
        def _update():
            status = progress_data.get("status")
            if status == "downloading":
                percent = progress_data.get("percent", 0) / 100.0
                self.file_progress_bar.set(percent)

                speed_str = progress_data.get("speed_str", "")
                eta_str = progress_data.get("eta_str", "")
                downloaded_str = progress_data.get("downloaded_str", "")
                total_str = progress_data.get("total_str", "")
                filename = progress_data.get("filename", "")

                lbl_text = f"Downloading: {filename} | {int(percent*100)}% ({downloaded_str} / {total_str}) @ {speed_str} | ETA: {eta_str}"
                self.file_progress_lbl.configure(text=lbl_text)
                self.status_lbl.configure(text=f"Status: Downloading ({int(percent*100)}%)")
        self.after(0, _update)

    def _check_ffmpeg_status(self):
        has_ff = check_ffmpeg()
        if has_ff:
            self.ffmpeg_badge.configure(text="FFmpeg: Available ✅", text_color="#2ecc71")
        else:
            self.ffmpeg_badge.configure(text="FFmpeg: Not Found ⚠️", text_color="#e74c3c")
            self.log("System Notice: FFmpeg binary not detected on PATH. Audio conversions will rely on fallback formats.")

    def _toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() == 1 else "Light"
        ctk.set_appearance_mode(mode)
        self.config_data["theme_mode"] = mode
        save_config(self.config_data)

    def _on_format_changed(self, value):
        if value == "Audio Only":
            self.res_dropdown.configure(state="disabled")
            self.audio_dropdown.configure(state="normal")
            self.sublang_dropdown.configure(state="disabled")
            self.subfmt_dropdown.configure(state="disabled")
        elif value == "Transcript Only":
            self.res_dropdown.configure(state="disabled")
            self.audio_dropdown.configure(state="disabled")
            self.sublang_dropdown.configure(state="normal")
            self.subfmt_dropdown.configure(state="normal")
        else:
            self.res_dropdown.configure(state="normal")
            self.audio_dropdown.configure(state="normal")
            self.sublang_dropdown.configure(state="normal")
            self.subfmt_dropdown.configure(state="normal")

    def _paste_clipboard(self):
        try:
            clipboard_text = self.clipboard_get()
            self.url_input.delete(0, "end")
            self.url_input.insert(0, clipboard_text.strip())
        except Exception:
            pass

    def _browse_download_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, folder)

    def _copy_log(self):
        log_content = self.monitor_log.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(log_content)
        messagebox.showinfo("Clipboard", "Terminal logs copied to clipboard!")

    def _clear_log(self):
        self.monitor_log.delete("1.0", "end")

    def _open_output_folder(self):
        folder = self.dir_entry.get().strip() or self.config_data.get("download_dir")
        if os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        else:
            messagebox.showwarning("Warning", f"Directory does not exist: {folder}")

    def _load_batch_links(self):
        raw_text = self.batch_text.get("1.0", "end").strip()
        lines = [line.strip() for line in raw_text.splitlines() if line.strip() and not line.strip().startswith("#")]
        if lines:
            first_url = lines[0]
            self.url_input.delete(0, "end")
            self.url_input.insert(0, first_url)
            self.tabview.set("📥 Downloader & Syncer")
            self.log(f"Loaded {len(lines)} URL(s) from batch queue into pipeline.")
            self.queue_items = lines

    def _save_cloud_credentials(self):
        self.config_data["mega_email"] = self.mega_email_entry.get().strip()
        self.config_data["mega_password"] = self.mega_pass_entry.get().strip()
        self.config_data["telegram_bot_token"] = self.tg_bot_entry.get().strip()
        self.config_data["telegram_chat_id"] = self.tg_chat_entry.get().strip()
        self.config_data["telegram_api_id"] = self.tg_api_id_entry.get().strip()
        self.config_data["telegram_api_hash"] = self.tg_api_hash_entry.get().strip()
        if save_config(self.config_data):
            messagebox.showinfo("Success", "Cloud credentials saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save configuration file.")

    def _save_global_settings(self):
        self.config_data["write_thumbnail"] = self.write_thumb_var.get()
        self.config_data["write_info_json"] = self.write_json_var.get()
        self.config_data["download_dir"] = self.dir_entry.get().strip()
        self.config_data["delete_local_after_upload"] = self.delete_cache_var.get()
        if save_config(self.config_data):
            messagebox.showinfo("Success", "Settings saved successfully!")

    def _test_mega_connection(self):
        email = self.mega_email_entry.get().strip()
        password = self.mega_pass_entry.get().strip()
        if not email or not password:
            messagebox.showwarning("Warning", "Please enter MEGA email and password first.")
            return
        
        def _worker():
            try:
                from mega import Mega
                m = Mega().login(email, password)
                self.log("MEGA Test Connection: SUCCESS! Logged in.")
                messagebox.showinfo("MEGA Test", "Login Successful!")
            except Exception as e:
                self.log(f"MEGA Test Connection FAILED: {e}")
                messagebox.showerror("MEGA Test", f"Login Failed: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _test_telegram_connection(self):
        token = self.tg_bot_entry.get().strip()
        chat_id = self.tg_chat_entry.get().strip()
        if not token:
            messagebox.showwarning("Warning", "Please enter Telegram Bot Token.")
            return

        def _worker():
            try:
                url = f"https://api.telegram.org/bot{token}/getMe"
                res = requests.get(url, timeout=10).json()
                if res.get("ok"):
                    bot_name = res["result"].get("username")
                    self.log(f"Telegram Test Connection: SUCCESS! Connected to bot @{bot_name}")
                    messagebox.showinfo("Telegram Test", f"Connected to @{bot_name} successfully!")
                else:
                    self.log(f"Telegram Test FAILED: {res.get('description')}")
                    messagebox.showerror("Telegram Test", f"Failed: {res.get('description')}")
            except Exception as e:
                self.log(f"Telegram Test FAILED: {e}")
                messagebox.showerror("Telegram Test", f"Error: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _load_config_into_ui(self):
        pass

    # ---------------- PIPELINE EXECUTION ----------------
    def start_pipeline(self):
        if self.is_processing:
            return

        url_input_val = self.url_input.get().strip()
        urls_to_process = self.queue_items if self.queue_items else ([url_input_val] if url_input_val else [])

        if not urls_to_process:
            self.log("Error: Target URL field is empty. Please enter or paste a valid link.")
            messagebox.showwarning("Warning", "Please enter a valid URL.")
            return

        self.is_processing = True
        self.action_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.file_progress_bar.set(0)
        self.status_lbl.configure(text="Status: Initializing Pipeline...")

        threading.Thread(target=self._run_pipeline_thread, args=(urls_to_process,), daemon=True).start()

    def cancel_pipeline(self):
        if self.current_engine:
            self.current_engine.cancel()
        if self.current_syncer:
            self.current_syncer.cancel()
        self.log("Cancellation request submitted.")

    def _run_pipeline_thread(self, urls):
        try:
            chosen_format = self.format_var.get()
            resolution = self.res_var.get()
            audio_codec = self.audio_var.get()
            sub_lang = self.sublang_var.get()
            sub_format = self.subfmt_var.get()
            dest_target = self.dest_var.get()
            target_dir = self.dir_entry.get().strip() or self.config_data.get("download_dir")
            cache_dir = self.config_data.get("cache_dir", "advanced_cache")
            delete_cache = self.delete_cache_var.get()

            self.log(f"Initializing Downloader... Format: [{chosen_format}], Quality: [{resolution}], Target: [{dest_target}]")

            # Step 1: Download phase
            self.current_engine = DownloaderEngine(
                output_dir=cache_dir,
                format_mode=chosen_format,
                resolution=resolution,
                audio_codec=audio_codec,
                sub_lang=sub_lang,
                sub_format=sub_format,
                write_thumb=self.config_data.get("write_thumbnail", True),
                write_json=self.config_data.get("write_info_json", False),
                progress_callback=self.update_progress_ui,
                log_callback=self.log
            )

            downloaded_files = self.current_engine.download(urls)

            if self.current_engine.cancelled:
                self.log("Pipeline stopped due to cancellation.")
                self._finish_pipeline("Cancelled")
                return

            if not downloaded_files:
                self.log("No files were compiled or downloaded.")
                self._finish_pipeline("Finished with no files")
                return

            # Step 2: Cloud / Local Sync Phase
            self.log("Starting asset sync & distribution phase...")
            self.status_lbl.configure(text="Status: Syncing Files...")
            self.current_syncer = CloudSyncer(log_callback=self.log)

            if dest_target in ["Local Disk", "Local + Cloud"]:
                self.current_syncer.sync_local(downloaded_files, target_dir, delete_source=False)

            if dest_target in ["MEGA.nz", "Local + Cloud"]:
                email = self.config_data.get("mega_email")
                pwd = self.config_data.get("mega_password")
                self.current_syncer.sync_mega(downloaded_files, email, pwd, delete_source=delete_cache)

            if dest_target in ["Telegram", "Local + Cloud"]:
                bot_token = self.config_data.get("telegram_bot_token")
                chat_id = self.config_data.get("telegram_chat_id")
                api_id = self.config_data.get("telegram_api_id")
                api_hash = self.config_data.get("telegram_api_hash")

                if bot_token and chat_id:
                    self.current_syncer.sync_telegram_bot(downloaded_files, bot_token, chat_id, delete_source=delete_cache)
                elif api_id and api_hash:
                    self.current_syncer.sync_telegram_pyrogram(downloaded_files, api_id, api_hash, chat_id, delete_source=delete_cache)
                else:
                    self.log("Error: Telegram credentials missing in Cloud Credentials tab.")

            # If user selected Local Disk only and wants to move from cache to target_dir:
            if dest_target == "Local Disk":
                self.current_syncer.sync_local(downloaded_files, target_dir, delete_source=True)

            self.log("Pipeline execution successfully completed!")
            self._finish_pipeline("Completed Successfully ✅")

        except Exception as e:
            self.log(f"Pipeline Execution Exception: {e}")
            self._finish_pipeline(f"Error: {e}")

    def _finish_pipeline(self, status_msg):
        def _reset():
            self.is_processing = False
            self.current_engine = None
            self.current_syncer = None
            self.queue_items = []
            self.action_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self.status_lbl.configure(text=f"Status: {status_msg}")
            self.file_progress_lbl.configure(text="Idle")
        self.after(0, _reset)

if __name__ == "__main__":
    app = UltimateMediaCloudSyncer()
    app.mainloop()