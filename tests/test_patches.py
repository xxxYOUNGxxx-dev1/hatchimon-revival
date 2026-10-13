"""Exercise repeat builds and API-conditional receiver registration."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('patcher', ROOT / 'scripts/patch_android16.py')
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)

class PatchTests(unittest.TestCase):
    def test_repeat_build_and_receiver_branches(self):
        with tempfile.TemporaryDirectory() as tmp:
            guest = Path(tmp)
            fixtures = {
                'com/unity3d/ads/connectivity/ConnectivityMonitor.smali': '\n'.join(
                    'invoke-virtual {' + reg + '}, Landroid/telephony/TelephonyManager;->getNetworkType()I'
                    for reg in ['v2', 'v3']),
                'com/unity3d/ads/device/Device.smali': 'invoke-virtual {v0}, Landroid/telephony/TelephonyManager;->getNetworkType()I',
                'com/google/android/gms/internal/zzni$zza.smali': 'invoke-virtual {v0}, Landroid/telephony/TelephonyManager;->getNetworkType()I',
                'com/vungle/publisher/ci.smali': '.method public a()V\n    .locals 3\n    invoke-virtual {v0, p0, v1}, Landroid/content/Context;->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;\n.end method\n',
            }
            for name, text in fixtures.items():
                p = guest / 'smali' / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding='utf-8')
            patcher.apply_patches(guest)
            first = {name: (guest/'smali'/name).read_bytes() for name in fixtures}
            patcher.apply_patches(guest)
            self.assertEqual(first, {name: (guest/'smali'/name).read_bytes() for name in fixtures})
            monitor = first[next(iter(fixtures))].decode()
            self.assertEqual(monitor.count('.method public static safeNetworkType('), 1)
            self.assertIn('.catch Ljava/lang/SecurityException;', monitor)
            self.assertEqual(monitor.count('invoke-virtual'), 1)  # Only inside guarded helper.
            receiver = first['com/vungle/publisher/ci.smali'].decode()
            self.assertIn('.locals 4', receiver)
            self.assertIn('const/16 v2, 0x21', receiver)
            self.assertIn('if-lt v3, v2, :vungle_receiver_legacy', receiver)
            self.assertIn('const/4 v3, 0x4', receiver)
            self.assertEqual(receiver.count('->registerReceiver('), 2)

if __name__ == '__main__':
    unittest.main()
