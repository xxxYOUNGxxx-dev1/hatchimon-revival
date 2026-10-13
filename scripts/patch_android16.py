"""Apply Android compatibility fixes; safe to run repeatedly."""
from pathlib import Path
import argparse

def apply_patches(guest):
    path=guest/'smali/com/unity3d/ads/connectivity/ConnectivityMonitor.smali'
    s=path.read_text(encoding='utf-8')
    for reg in ['v2','v3']:
        s=s.replace('invoke-virtual {'+reg+'}, Landroid/telephony/TelephonyManager;->getNetworkType()I',
                    'invoke-static {'+reg+'}, Lcom/unity3d/ads/connectivity/ConnectivityMonitor;->safeNetworkType(Landroid/telephony/TelephonyManager;)I')
    if '.method public static safeNetworkType(' not in s and '.method private static safeNetworkType(' not in s:
        s+='''
    .method public static safeNetworkType(Landroid/telephony/TelephonyManager;)I
        .locals 1
        if-eqz p0, :unknown
        :try_start_network
        invoke-virtual {p0}, Landroid/telephony/TelephonyManager;->getNetworkType()I
        move-result v0
        :try_end_network
        .catch Ljava/lang/SecurityException; {:try_start_network .. :try_end_network} :denied
        return v0
        :denied
        move-exception v0
        :unknown
        const/4 v0, 0x0
        return v0
    .end method
    '''
    s=s.replace('.method private static safeNetworkType(','.method public static safeNetworkType(')
    path.write_text(s,encoding='utf-8')
    for relative in ['com/unity3d/ads/device/Device.smali','com/google/android/gms/internal/zzni$zza.smali']:
        other=guest/'smali'/relative
        code=other.read_text(encoding='utf-8')
        code=code.replace('invoke-virtual {v0}, Landroid/telephony/TelephonyManager;->getNetworkType()I',
                          'invoke-static {v0}, Lcom/unity3d/ads/connectivity/ConnectivityMonitor;->safeNetworkType(Landroid/telephony/TelephonyManager;)I')
        other.write_text(code,encoding='utf-8')
    print('Patched Unity connectivity monitoring: refused phone-state access yields NETWORK_TYPE_UNKNOWN.')
    path=guest/'smali/com/vungle/publisher/ci.smali'
    s=path.read_text(encoding='utf-8')
    if ':vungle_receiver_legacy' not in s:
        s=s.replace('.method public a()V\n    .locals 3','.method public a()V\n    .locals 4',1)
        old='invoke-virtual {v0, p0, v1}, Landroid/content/Context;->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;)Landroid/content/Intent;'
        new='''sget v3, Landroid/os/Build$VERSION;->SDK_INT:I
        const/16 v2, 0x21
        if-lt v3, v2, :vungle_receiver_legacy
        # This receiver listens only for Vungle's local DUMP_TABLES action.
        const/4 v3, 0x4
        invoke-virtual {v0, p0, v1, v3}, Landroid/content/Context;->registerReceiver(Landroid/content/BroadcastReceiver;Landroid/content/IntentFilter;I)Landroid/content/Intent;
        goto :vungle_receiver_registered
        :vungle_receiver_legacy
        '''+old+'''
        :vungle_receiver_registered'''
        assert s.count(old)==1
        s=s.replace(old,new)
    path.write_text(s,encoding='utf-8')
    print('Patched Vungle internal receiver registration with RECEIVER_NOT_EXPORTED on API 33+.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decoded", type=Path, default=Path(__file__).resolve().parents[1]/".work/guest-decoded")
    apply_patches(parser.parse_args().decoded)
