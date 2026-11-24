# 08 — Actions, plugins and service integrations

## 23 desktop action modules found

All links point to source under `actions/` in the desktop repo.

| Module | Capability |
|---|---|
| [background_monitor.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/background_monitor.py) | Background monitoring |
| [background_tasks.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/background_tasks.py) | Long-running/background tasks |
| [browser_control.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/browser_control.py) | Browser navigation/control via Playwright |
| [code_helper.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/code_helper.py) | Coding assistance |
| [computer_control.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/computer_control.py) | Mouse, keyboard, clipboard and computer input |
| [computer_settings.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/computer_settings.py) | OS/computer settings |
| [desktop.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/desktop.py) | Desktop application interactions |
| [dev_agent.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/dev_agent.py) | Developer agent operations |
| [file_controller.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/file_controller.py) | File operations |
| [file_processor.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/file_processor.py) | File/document extraction and processing |
| [flight_finder.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/flight_finder.py) | Flight search |
| [game_updater.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/game_updater.py) | Game/update operations |
| [open_app.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/open_app.py) | Launch applications |
| [proactive.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/proactive.py) | Proactive assistance |
| [reminder.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/reminder.py) | Reminder operations |
| [routines.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/routines.py) | Routines/scheduled actions |
| [screen_processor.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/screen_processor.py) | Screen/camera capture and processing |
| [send_message.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/send_message.py) | Message sending |
| [system_monitor.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/system_monitor.py) | System/hardware monitoring |
| [video_player.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/video_player.py) | Video playback |
| [weather_report.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/weather_report.py) | Weather reporting |
| [web_search.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/web_search.py) | Web/news search |
| [youtube_video.py](https://github.com/tarikk786786/DAZY-ai-new/blob/main/actions/youtube_video.py) | YouTube video/transcript functionality |

Actual exposure to the model is governed by each module's `TOOL` declaration and action discovery, not simply by the filename existing.

## Plugins found

- `plugins/automation.py` — Activepieces workflow status/list/draft/publish/advisor operations. Publishing is a consequential action; user approval policy should remain enabled.
- `plugins/gmail.py` — checks recent unread email or creates a draft via Gmail integration.
- `plugins/public_apis.py` — public API lookup for weather, Wikipedia and Quran.
- `plugins/telegram.py` — Telegram alerts/messages.
- `plugins/_template.py` — plugin template.

## Integrations found

- Google Gmail: `integrations/google/gmail.py` and Google auth packages.
- Telegram: `integrations/communication/telegram.py` and plugin.
- Wikipedia: `integrations/research/wikipedia.py`.
- Open-Meteo weather: `integrations/utilities/weather.py`.
- Quran: `integrations/knowledge/quran.py`.
- Activepieces: automation manager + MCP adapter.
- API discovery: `integrations/api_discovery.py` and `plugins/public_apis.py`.
- Auth manager, credential manager and generic HTTP client.
- Supabase sync: `memory/supabase_sync.py`.

The existence of an integration does not confirm OAuth has been completed, API keys are configured, a remote service is reachable or a user has granted permission.
