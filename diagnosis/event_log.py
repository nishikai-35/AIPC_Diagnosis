import subprocess
import json


def get_event_logs_for_log_name(log_name, hours=24, limit=20):
    """
    指定したWindowsイベントログから
    Error / Warningを取得する
    """

    powershell_script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$startTime = (Get-Date).AddHours(-{hours})

Get-WinEvent -FilterHashtable @{{
    LogName='{log_name}'
    StartTime=$startTime
    Level=2,3
}} |
Select-Object -First {limit} `
    TimeCreated,
    LogName,
    ProviderName,
    Id,
    Level,
    LevelDisplayName,
    Message |
ForEach-Object {{
    [PSCustomObject]@{{
        TimeCreated = $_.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")
        LogName = $_.LogName
        ProviderName = $_.ProviderName
        Id = $_.Id
        Level = $_.Level
        LevelDisplayName = $_.LevelDisplayName
        Message = $_.Message
    }}
}} |
ConvertTo-Json -Depth 3 -Compress
"""

    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        powershell_script,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )

        if result.returncode != 0:
            print(
                f"[EventLog] PowerShell error ({log_name}):"
            )
            print(result.stderr)
            return []

        output = result.stdout.strip()

        if not output:
            return []

        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            print(
                f"[EventLog] JSON decode error ({log_name}): {e}"
            )
            print("PowerShell output:")
            print(output[:2000])
            return []

        if isinstance(data, dict):
            data = [data]

        return data

    except subprocess.TimeoutExpired:
        print(
            f"[EventLog] Timeout ({log_name})"
        )
        return []

    except Exception as e:
        print(
            f"[EventLog] Unexpected error ({log_name}): {e}"
        )
        return []


def get_windows_event_logs(hours=24, limit=20):
    """
    System / ApplicationのWindowsイベントログを取得する
    """

    system_events = get_event_logs_for_log_name(
        "System",
        hours=hours,
        limit=limit,
    )

    application_events = get_event_logs_for_log_name(
        "Application",
        hours=hours,
        limit=limit,
    )

    events = system_events + application_events

    # 新しいイベント順に並べる
    events.sort(
        key=lambda event: str(event.get("TimeCreated", "")),
        reverse=True,
    )

    return events[:limit]