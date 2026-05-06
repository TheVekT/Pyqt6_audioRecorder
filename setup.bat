@echo off
rem 
cd /d %~dp0

powershell -Command "Invoke-WebRequest -Uri 'https://github.com/TheVekT/Pyqt6_audioRecorder/releases/latest/download/Audio.Recorder.exe' -OutFile 'AudioRecorder.exe'"

echo.
echo Download complete!
echo.

pause