#!/usr/bin/env python3
"""tools/audio_diagnostics.py — Comprehensive Windows Audio, PortAudio & Microphone Diagnostic Tool.

Part of DAZY Master Emergency Audio Repair Suite.
Measures real hardware, PortAudio streams, device capabilities, callback rates,
and performs an in-memory 5-second microphone sample test without saving audio to disk.
"""
import sys
import time
import math
from pathlib import Path
import numpy as np

def run_diagnostics():
    print("=" * 70)
    print("  DAZY MASTER AUDIO & MICROPHONE HARDWARE DIAGNOSTIC")
    print("=" * 70)

    # 1. Python Interpreter & Packages
    print("\n[1] Python Runtime & Audio Packages:")
    print(f"  - Interpreter Path: {sys.executable}")
    print(f"  - Python Version:   {sys.version.split()[0]}")

    packages = ["sounddevice", "numpy", "google.genai", "miniaudio"]
    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "installed")
            print(f"  - {pkg:<16}: {version}")
        except ImportError:
            print(f"  - {pkg:<16}: NOT INSTALLED")

    # 2. PortAudio Version
    import sounddevice as sd
    pa_version = sd.get_portaudio_version()
    print(f"\n[2] PortAudio Driver: {pa_version[0]}")

    # 3. Host APIs
    print("\n[3] Available Host APIs:")
    host_apis = sd.query_hostapis()
    for idx, api in enumerate(host_apis):
        print(f"  [{idx}] {api['name']:<25} (Devices: {len(api['devices'])}, Default In: {api['default_input_device']}, Default Out: {api['default_output_device']})")

    # 4. Device Enumeration
    devices = sd.query_devices()
    default_in = sd.default.device[0]
    default_out = sd.default.device[1]
    print(f"\n[4] Audio Device Catalog (Total: {len(devices)}):")
    print(f"  Default Input Device:  [{default_in}] {devices[default_in]['name'] if default_in >= 0 else 'None'}")
    print(f"  Default Output Device: [{default_out}] {devices[default_out]['name'] if default_out >= 0 else 'None'}")

    sample_rates_to_test = [16000, 24000, 44100, 48000]

    print("\n  Input Devices Detected:")
    for idx, d in enumerate(devices):
        if d['max_input_channels'] > 0:
            is_def = " (DEFAULT)" if idx == default_in else ""
            api_name = host_apis[d['hostapi']]['name']
            print(f"  -> [{idx}] {d['name']}{is_def}")
            print(f"       Host API: {api_name} | Max Channels: {d['max_input_channels']} | Default SR: {d['default_samplerate']} Hz")
            supported = []
            for sr in sample_rates_to_test:
                try:
                    sd.check_input_settings(device=idx, channels=1, dtype='int16', samplerate=sr)
                    supported.append(f"{sr}Hz")
                except Exception:
                    pass
            print(f"       Supported 1ch int16 SRs: {', '.join(supported) if supported else 'None'}")

    print("\n  Output Devices Detected:")
    for idx, d in enumerate(devices):
        if d['max_output_channels'] > 0:
            is_def = " (DEFAULT)" if idx == default_out else ""
            api_name = host_apis[d['hostapi']]['name']
            print(f"  -> [{idx}] {d['name']}{is_def}")
            print(f"       Host API: {api_name} | Max Channels: {d['max_output_channels']} | Default SR: {d['default_samplerate']} Hz")

    # 5. Live Stream & Callback Capture Test (5 Seconds)
    print("\n" + "=" * 70)
    print("  [5] LIVE HARDWARE MICROPHONE TEST (5 SECONDS)")
    print("=" * 70)

    if default_in < 0:
        print("  [ERROR] No default input device available!")
        return False

    dev_info = devices[default_in]
    target_sr = 16000
    channels = 1
    dtype = 'int16'
    chunk_size = 512

    # Check settings first
    try:
        sd.check_input_settings(device=default_in, channels=channels, dtype=dtype, samplerate=target_sr)
        print(f"  [OK] Input settings verified: Device [{default_in}] {dev_info['name']} @ {target_sr} Hz, 1 channel, int16")
    except Exception as exc:
        print(f"  [WARNING] Direct 16kHz input check failed: {exc}")
        print(f"  Will test at native device rate {int(dev_info['default_samplerate'])} Hz")
        target_sr = int(dev_info['default_samplerate'])

    callbacks_fired = 0
    total_samples = 0
    clipped_samples = 0
    silent_frames = 0
    overflow_count = 0
    all_rms = []
    max_peak = 0

    def audio_callback(indata, frames, time_info, status):
        nonlocal callbacks_fired, total_samples, clipped_samples, silent_frames, overflow_count, max_peak
        callbacks_fired += 1
        if status.input_overflow:
            overflow_count += 1
        
        # Audio frame analysis
        samples = indata.flatten()
        total_samples += len(samples)
        peak = int(np.max(np.abs(samples))) if len(samples) > 0 else 0
        if peak > max_peak:
            max_peak = peak
        
        # Check clipping for int16 (max 32767)
        clipped = np.sum(np.abs(samples) >= 32760)
        clipped_samples += int(clipped)

        # Calculate RMS
        if len(samples) > 0:
            rms = math.sqrt(np.mean(samples.astype(np.float64) ** 2))
            all_rms.append(rms)
            if rms < 20.0:  # Noise floor threshold for int16
                silent_frames += 1

    print(f"\n  Starting 5-second audio capture from [{default_in}] '{dev_info['name']}'...")
    print("  >>> PLEASE SPEAK OR TAP THE MICROPHONE NOW <<<")
    
    t0 = time.time()
    try:
        with sd.InputStream(device=default_in, channels=channels, samplerate=target_sr,
                            dtype=dtype, blocksize=chunk_size, callback=audio_callback):
            while time.time() - t0 < 5.0:
                time.sleep(0.1)
                elapsed = time.time() - t0
                current_peak = max_peak
                bars = "#" * min(40, int(current_peak / 800))
                sys.stdout.write(f"\r  [{elapsed:.1f}s / 5.0s] Callbacks: {callbacks_fired} | Peak: {current_peak:5d} | Level: {bars:<40}")
                sys.stdout.flush()
    except Exception as exc:
        print(f"\n  [FAILURE] Could not open InputStream: {exc}")
        return False

    print("\n\n" + "=" * 70)
    print("  MICROPHONE CAPTURE ANALYSIS RESULTS")
    print("=" * 70)
    avg_rms = np.mean(all_rms) if all_rms else 0.0
    silent_pct = (silent_frames / callbacks_fired * 100.0) if callbacks_fired > 0 else 100.0
    clip_pct = (clipped_samples / total_samples * 100.0) if total_samples > 0 else 0.0

    print(f"  - Total Duration:         {time.time() - t0:.2f} s")
    print(f"  - Callbacks Fired:        {callbacks_fired} (Expected: ~{int(5.0 * target_sr / chunk_size)})")
    print(f"  - Total Samples Captured: {total_samples}")
    print(f"  - Peak Amplitude:         {max_peak} / 32767 ({max_peak / 32767 * 100.0:.1f}% FS)")
    print(f"  - Average RMS:            {avg_rms:.1f} ({20 * math.log10(max(avg_rms, 1) / 32768):.1f} dBFS)")
    print(f"  - Silent Frame Ratio:     {silent_pct:.1f}%")
    print(f"  - Clipping Ratio:         {clip_pct:.2f}%")
    print(f"  - Input Overflows:        {overflow_count}")

    if callbacks_fired == 0:
        print("\n  [CRITICAL FAILURE] Audio callback NEVER fired! PortAudio or device stream is stalled.")
        return False
    elif max_peak == 0:
        print("\n  [CRITICAL FAILURE] Microphone returned absolute zeros! Hardware mute or Windows Privacy blockage.")
        return False
    elif max_peak < 100:
        print("\n  [WARNING] Extremely low signal detected (Peak < 100). Microphone volume may be too low.")
        return True
    else:
        print("\n  [PASS] Real microphone audio successfully captured and measured!")
        return True

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
