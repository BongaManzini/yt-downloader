import os
import shutil
import requests
from mega import Mega

class CloudSyncer:
    def __init__(self, log_callback=None, progress_callback=None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.cancelled = False

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(f"[*] {msg}")

    def cancel(self):
        self.cancelled = True
        self.log("Cancellation signal received in CloudSyncer.")

    def sync_local(self, file_paths, target_dir, delete_source=False):
        os.makedirs(target_dir, exist_ok=True)
        synced_files = []
        total = len(file_paths)
        for idx, src in enumerate(file_paths, start=1):
            if self.cancelled:
                self.log("Local sync cancelled.")
                break
            filename = os.path.basename(src)
            dest = os.path.join(target_dir, filename)
            self.log(f"[{idx}/{total}] Copying to Local Disk: {filename}")
            try:
                if delete_source:
                    shutil.move(src, dest)
                else:
                    shutil.copy2(src, dest)
                synced_files.append(dest)
            except Exception as e:
                self.log(f"Error copying {filename}: {e}")
        return synced_files

    def sync_mega(self, file_paths, email, password, delete_source=False):
        if not email or not password:
            self.log("Error: MEGA credentials missing. Please set email and password in Cloud Settings.")
            return False

        try:
            self.log("Logging into MEGA.nz...")
            mega = Mega()
            m = mega.login(email, password)
            self.log("MEGA login successful!")

            total = len(file_paths)
            for idx, filepath in enumerate(file_paths, start=1):
                if self.cancelled:
                    self.log("MEGA sync cancelled.")
                    break
                filename = os.path.basename(filepath)
                self.log(f"[{idx}/{total}] Uploading to MEGA: {filename}...")

                # Mega upload
                file_node = m.upload(filepath)
                try:
                    link = m.get_upload_link(file_node)
                    self.log(f"-> Uploaded! Link: {link}")
                except Exception:
                    self.log(f"-> Uploaded {filename} successfully.")

                if delete_source:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass

            self.log("MEGA Synchronization complete.")
            return True

        except Exception as e:
            self.log(f"MEGA Synchronization Error: {e}")
            return False

    def sync_telegram_bot(self, file_paths, bot_token, chat_id, delete_source=False):
        if not bot_token or not chat_id:
            self.log("Error: Telegram Bot Token or Chat ID missing. Please set them in Cloud Settings.")
            return False

        base_url = f"https://api.telegram.org/bot{bot_token}"
        total = len(file_paths)
        success_count = 0

        for idx, filepath in enumerate(file_paths, start=1):
            if self.cancelled:
                self.log("Telegram upload cancelled.")
                break

            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            self.log(f"[{idx}/{total}] Uploading to Telegram Bot: {filename} ({file_size / (1024*1024):.1f} MB)...")

            # Telegram Bot API max file size limit for bots is 50MB
            if file_size > 50 * 1024 * 1024:
                self.log(f"Warning: {filename} exceeds 50MB Bot API limit. Telegram Bot upload skipped.")
                continue

            endpoint = "sendDocument"
            file_type = "document"

            if filepath.lower().endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov')):
                endpoint = "sendVideo"
                file_type = "video"
            elif filepath.lower().endswith(('.mp3', '.m4a', '.wav', '.flac', '.ogg')):
                endpoint = "sendAudio"
                file_type = "audio"

            try:
                with open(filepath, 'rb') as f:
                    files = {file_type: (filename, f)}
                    data = {'chat_id': chat_id, 'caption': f"Asset: {filename}"}
                    response = requests.post(f"{base_url}/{endpoint}", data=data, files=files, timeout=300)
                    res_json = response.json()
                    if res_json.get("ok"):
                        self.log(f"-> Sent to Telegram successfully!")
                        success_count += 1
                        if delete_source:
                            try:
                                os.remove(filepath)
                            except Exception:
                                pass
                    else:
                        self.log(f"Telegram Bot API Error: {res_json.get('description')}")
            except Exception as e:
                self.log(f"Telegram upload failed for {filename}: {e}")

        self.log(f"Telegram Bot sync completed ({success_count}/{total} files uploaded).")
        return success_count > 0

    def sync_telegram_pyrogram(self, file_paths, api_id, api_hash, chat_id="me", delete_source=False):
        if not api_id or not api_hash:
            self.log("Error: Telegram API ID or API Hash missing.")
            return False

        try:
            from pyrogram import Client
            self.log("Initializing Pyrogram client...")
            session_path = os.path.join(os.path.dirname(__file__), "yt_down_session")
            with Client(session_path, int(api_id), api_hash) as app:
                total = len(file_paths)
                for idx, filepath in enumerate(file_paths, start=1):
                    if self.cancelled:
                        self.log("Telegram pyrogram upload cancelled.")
                        break

                    filename = os.path.basename(filepath)
                    self.log(f"[{idx}/{total}] Uploading to Telegram Cloud: {filename}...")

                    target_chat = chat_id if chat_id else "me"
                    if filepath.endswith(('.vtt', '.srt', '.txt')):
                        app.send_document(target_chat, document=filepath, caption=f"Transcript: {filename}")
                    elif filepath.endswith(('.m4a', '.mp3', '.wav', '.flac', '.ogg')):
                        app.send_audio(target_chat, audio=filepath, caption=f"Audio: {filename}")
                    else:
                        app.send_video(target_chat, video=filepath, caption=f"Video: {filename}")

                    self.log(f"-> Uploaded {filename} to Telegram.")

                    if delete_source:
                        try:
                            os.remove(filepath)
                        except Exception:
                            pass

            self.log("Telegram Pyrogram Cloud sync complete.")
            return True
        except Exception as e:
            self.log(f"Pyrogram Telegram error: {e}")
            return False
