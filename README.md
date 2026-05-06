# Audio.Recorder

A simple, lightweight audio recorder designed for long-term background monitoring and room recording. It focuses on stability and minimal disk space usage rather than high-fidelity audio.

## Key Features

- **Long-term Background Recording**: Optimized for continuous use in the background.
- **Time-based Splitting**: Automatically cuts recordings into chunks (10, 30, 60, or 120 minutes) to keep file sizes manageable.
- **Efficient Audio**: Saves mono 22kHz WAV files to minimize disk space consumption.
- **Sound Activity Monitor**: A visual indicator changes color when sound is detected in the room.
- **Auto-Cleanup**: Automatically removes old recordings after a set number of days to prevent disk overflow.
- **Mini-Mode**: A small, compact window that can stay on top of other applications.
- **Simple Gain Control**: Boost input volume if the source is quiet.

## Download & Quick Start

If you don't want to run the source code, you can download the pre-compiled version from the **Releases** section:
- [**Audio.Recorder.exe**](https://github.com/TheVekT/Pyqt6_audioRecorder/releases/latest/download/Audio.Recorder.exe): A standalone executable for Windows. Just download and run - no installation required.

---

## Requirements (for running from source)

- Python 3.10+
- PyQt6
- NumPy

## Usage

- **Select Folder**: Choose where you want to save the recordings.
- **Set Retention**: Use the slider to choose how many days to keep the files.
- **Choose Device**: Select your microphone from the dropdown list.
- **Start**: Press the start button. The application will handle the rest, including file splitting and old file removal.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
