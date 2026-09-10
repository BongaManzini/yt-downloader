import os
import shutil
import subprocess
from yt_dlp import YoutubeDL

def check_ffmpeg():
    return shutil.which("ffmpeg") is not None

def format_bytes(bytes_val):
    if not bytes_val:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"

def format_seconds(seconds):
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

class DownloaderEngine:
    def __init__(self, output_dir, format_mode="Video Only", resolution="Best Quality",
                 audio_codec="mp3", sub_lang="en", sub_format="srt",
                 write_thumb=True, write_json=False,
                 progress_callback=None, log_callback=None):
        self.output_dir = output_dir
        self.format_mode = format_mode
        self.resolution = resolution
        self.audio_codec = audio_codec
        self.sub_lang = sub_lang
        self.sub_format = sub_format
        self.write_thumb = write_thumb
        self.write_json = write_json
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.cancelled = False

    def log(self, msg):
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(f"[*] {msg}")

    def cancel(self):
        self.cancelled = True
        self.log("Cancellation signal received. Stopping download...")

    def ytdlp_hook(self, d):
        if self.cancelled:
            raise Exception("Operation cancelled by user.")

        status = d.get('status')
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            filename = os.path.basename(d.get('filename', 'Unknown'))

            percent = (downloaded / total * 100) if total > 0 else 0

            info_dict = d.get('info_dict', {})
            current_idx = info_dict.get('playlist_index')
            total_items = info_dict.get('n_entries')

            progress_data = {
                'status': 'downloading',
                'filename': filename,
                'downloaded': downloaded,
                'total': total,
                'percent': percent,
                'speed': speed,
                'eta': eta,
                'speed_str': f"{format_bytes(speed)}/s" if speed else "0 B/s",
                'eta_str': format_seconds(eta),
                'downloaded_str': format_bytes(downloaded),
                'total_str': format_bytes(total),
                'item_index': current_idx,
                'item_total': total_items
            }

            if self.progress_callback:
                self.progress_callback(progress_data)

        elif status == 'finished':
            filename = os.path.basename(d.get('filename', ''))
            self.log(f"Finished downloading fragment: {filename}")

    def download(self, urls):
        if isinstance(urls, str):
            urls = [urls]

        os.makedirs(self.output_dir, exist_ok=True)
        out_template = os.path.join(self.output_dir, '%(title)s.%(ext)s')

        has_ffmpeg = check_ffmpeg()
        if not has_ffmpeg:
            self.log("Warning: FFmpeg binary not found on PATH. Some conversions/merging may fail.")

        ydl_opts = {
            'outtmpl': out_template,
            'progress_hooks': [self.ytdlp_hook],
            'ignoreerrors': True,
            'nocheckcertificate': True,
        }

        # Resolution mapping
        res_limit = ""
        if "1080p" in self.resolution:
            res_limit = "[height<=1080]"
        elif "720p" in self.resolution:
            res_limit = "[height<=720]"
        elif "480p" in self.resolution:
            res_limit = "[height<=480]"

        # Format Logic
        if self.format_mode == "Video Only":
            if has_ffmpeg:
                ydl_opts['format'] = f'bestvideo{res_limit}[ext=mp4]+bestaudio[ext=m4a]/best{res_limit}[ext=mp4]/best{res_limit}'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                ydl_opts['format'] = f'best{res_limit}'

        elif self.format_mode == "Audio Only":
            ydl_opts['format'] = 'bestaudio/best'
            if has_ffmpeg:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': self.audio_codec if self.audio_codec in ['mp3', 'm4a', 'wav', 'flac'] else 'mp3',
                    'preferredquality': '192',
                }]

        elif self.format_mode == "Transcript Only":
            ydl_opts['skip_download'] = True
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [self.sub_lang] if self.sub_lang != "all" else ['all']
            if has_ffmpeg and self.sub_format in ['srt', 'vtt']:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': self.sub_format,
                }]

        elif self.format_mode == "Everything Combo":
            if has_ffmpeg:
                ydl_opts['format'] = f'bestvideo{res_limit}[ext=mp4]+bestaudio[ext=m4a]/best{res_limit}[ext=mp4]/best{res_limit}'
                ydl_opts['merge_output_format'] = 'mp4'
            else:
                ydl_opts['format'] = f'best{res_limit}'
            ydl_opts['writesubtitles'] = True
            ydl_opts['writeautomaticsub'] = True
            ydl_opts['subtitleslangs'] = [self.sub_lang] if self.sub_lang != "all" else ['all']
            ydl_opts['writethumbnail'] = self.write_thumb
            ydl_opts['writeinfojson'] = self.write_json
            if has_ffmpeg and self.sub_format in ['srt', 'vtt']:
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegSubtitlesConvertor',
                    'format': self.sub_format,
                }]

        downloaded_files = []
        try:
            with YoutubeDL(ydl_opts) as ydl:
                self.log(f"Starting extraction for {len(urls)} URL(s)...")
                ydl.download(urls)

            # Gather downloaded files in output_dir
            for root, _, files in os.walk(self.output_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    downloaded_files.append(full_p)

            self.log(f"Download phase completed. Total files in workspace: {len(downloaded_files)}")
            return downloaded_files

        except Exception as e:
            if "cancelled" in str(e).lower():
                self.log("Download cancelled by user.")
            else:
                self.log(f"Error during download: {e}")
            return downloaded_files
