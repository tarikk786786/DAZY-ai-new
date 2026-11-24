# 09 — Desktop, automation, computer use, vision and monitoring

## Computer and browser control

- Playwright: browser automation; Chromium/Firefox installation is attempted by `setup.py`.
- PyAutoGUI: mouse/keyboard control; configured with failsafe enabled in source.
- Pyperclip: clipboard operations.
- PyGetWindow: window geometry/window interaction.
- Pywinauto: Windows accessibility/UI automation (Windows-only dependency).
- pywin32, WMI, comtypes, pycaw: Windows integration, WMI, COM and audio-control support.
- `actions/browser_control.py`, `actions/computer_control.py`, `actions/computer_settings.py`, `actions/desktop.py`, `actions/open_app.py`, `actions/screen_processor.py`.

## Screen and visual pipeline

- Pillow — image operations.
- OpenCV — computer-vision/image processing.
- MSS — screen capture.
- MediaPipe is listed as optional in requirements comments for a push-up/pose feature; not installed by default.
- `core/screenview.py`, `core/screenact.py`, `core/ambient/screen_observer.py`, `actions/screen_processor.py`.
- `core/avatar.py`, `core/avatar_mesh.py`, `core/face_model.obj`, `core/viseme.py` support the visual avatar and mouth animation.

## Automation and scheduling

- `core/automation/manager.py` — automation management.
- `core/automation/planner.py` — plan workflows.
- `core/automation/approval.py` — approval gates.
- `core/automation/suggestion_engine.py` — suggested automations.
- `core/routines/engine.py`, `rules.py`, `desktop.py` — routine execution and rules.
- `core/scheduler_service.py` — scheduling.
- `actions/routines.py`, `actions/reminder.py`, `plugins/automation.py`.
- Activepieces is an external workflow service integration, not a bundled free unlimited service.

## Ambient intelligence and resources

- `core/ambient/governor.py` — resource governor.
- `core/ambient/proactive_alerts.py` — proactive alert logic.
- `core/ambient/screen_observer.py` — active-screen observation.
- `core/ambient/task_observer.py` — task observation.
- `actions/background_monitor.py`, `actions/system_monitor.py`.
- `psutil` — CPU/RAM/process/system statistics.
- `pynvml` — NVIDIA GPU telemetry (optional hardware-specific availability).

## Device and cross-device systems

- `core/devices/device_hub.py`
- `core/devices/models.py`
- `core/devices/pairing.py`
- `core/devices/nearby_discovery.py`
- `core/devices/handoff.py`
- `gui/devices_panel.py`
- `mobile/companion/dazy_mobile_client.py`
- `backend/app.py`

Docs describe QR/one-time-code pairing and task/context handoff. End-to-end iOS/Android native app delivery is not established by the repository paths inspected; mobile companion code is present.

## OS-aware support

`core/platform_support.py`, `core/appidentity.py`, `core/tls.py`, `core/hotkey.py`, `core/installer.py`, `core/lazyimport.py`. Setup declares Windows-only packages separately and describes macOS/Linux native-command fallbacks. Verify each action on the target OS before enabling it.
