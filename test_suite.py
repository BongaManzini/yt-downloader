import os
import shutil
import unittest

from config_manager import load_config, save_config, CONFIG_FILE
from downloader_engine import DownloaderEngine, check_ffmpeg, format_bytes, format_seconds
from cloud_syncer import CloudSyncer

class TestMediaCloudSyncer(unittest.TestCase):

    def test_format_helpers(self):
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_bytes(1048576), "1.00 MB")
        self.assertEqual(format_seconds(65), "01:05")

    def test_config_manager(self):
        cfg = load_config()
        self.assertIn("download_dir", cfg)
        self.assertIn("theme_mode", cfg)
        
        cfg["theme_mode"] = "Dark"
        save_config(cfg)
        loaded = load_config()
        self.assertEqual(loaded["theme_mode"], "Dark")

    def test_cloud_syncer_local(self):
        test_dir = os.path.join(os.path.dirname(__file__), "test_temp_src")
        target_dir = os.path.join(os.path.dirname(__file__), "test_temp_dst")
        os.makedirs(test_dir, exist_ok=True)
        os.makedirs(target_dir, exist_ok=True)

        test_file = os.path.join(test_dir, "sample.txt")
        with open(test_file, "w") as f:
            f.write("Hello Media Cloud Syncer Test")

        syncer = CloudSyncer()
        copied = syncer.sync_local([test_file], target_dir, delete_source=False)
        self.assertTrue(len(copied) == 1)
        self.assertTrue(os.path.exists(copied[0]))

        # Cleanup
        shutil.rmtree(test_dir)
        shutil.rmtree(target_dir)

    def test_ffmpeg_detection(self):
        has_ff = check_ffmpeg()
        print(f"FFmpeg detected in test: {has_ff}")

if __name__ == "__main__":
    unittest.main()
