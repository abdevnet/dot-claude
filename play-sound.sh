#!/bin/bash
# Cross-platform sound player for Claude Code hooks.
# Usage: play-sound.sh <permission|idle>

sound="$1"

play_windows() {
  local file="$1"
  local ext="${file##*.}"
  if [[ "${ext,,}" == "wav" ]]; then
    powershell.exe -NoProfile -Command "(New-Object Media.SoundPlayer '$file').PlaySync()" >/dev/null 2>&1
  else
    # MP3/other: use WPF MediaPlayer (async), then wait for the clip's natural duration.
    powershell.exe -NoProfile -Command "
      Add-Type -AssemblyName presentationCore;
      \$p = New-Object System.Windows.Media.MediaPlayer;
      \$p.Open([Uri]'$file');
      \$t = 50; while (-not \$p.NaturalDuration.HasTimeSpan -and \$t-- -gt 0) { Start-Sleep -Milliseconds 50 };
      \$p.Play();
      if (\$p.NaturalDuration.HasTimeSpan) { Start-Sleep -Milliseconds ([int]\$p.NaturalDuration.TimeSpan.TotalMilliseconds + 200) };
    " >/dev/null 2>&1
  fi
}

case "$(uname -s)" in
  Darwin)
    case "$sound" in
      permission) afplay "$HOME/.claude/sounds/permission.mp3" ;;
      idle)       afplay /System/Library/Sounds/Submarine.aiff ;;
    esac
    ;;
  MINGW*|MSYS*|CYGWIN*)
    case "$sound" in
      permission) play_windows 'C:\Users\abarker\.claude\sounds\permission.mp3' ;;
      idle)       play_windows 'C:\Windows\Media\Windows Notify.wav' ;;
    esac
    ;;
esac
