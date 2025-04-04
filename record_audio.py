import pyaudio
import wave
import threading
import keyboard  
import time
import numpy as np  
import os 

# Audio recording settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
GAIN = 10.0  

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.lock = threading.Lock()
        self.track_count = 0

    def start_recording(self):
        if self.recording:
            print("Already recording!")
            return

        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)
        self.frames = []
        self.recording = True
        print(f"Recording started. Press 's' to stop and save, 'q' to quit.")
        threading.Thread(target=self.record).start()

    def record(self):
        while self.recording:
            try:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                # Apply gain to increase volume
                amplified_data = self.apply_gain(data)
                with self.lock:
                    self.frames.append(amplified_data)
            except Exception as e:
                print(f"Error while recording: {e}")
                break

    def apply_gain(self, data):
        """Amplify the audio data by the GAIN factor."""
        try:
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplified_data = np.clip(audio_data * GAIN, -32768, 32767).astype(np.int16)
            return amplified_data.tobytes()
        except Exception as e:
            print(f"Error applying gain: {e}")
            return data  # Return original data if amplification fails

    def stop_recording(self):
        if not self.recording:
            print("Not currently recording!")
            return

        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        print("Recording stopped. Saving file...")
        self.save_file()

    def save_file(self):
        self.track_count += 1
        filename = f"track_{self.track_count}.wav"
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
            print(f"File saved as {filename}")
        except Exception as e:
            print(f"Error saving file: {e}")

    def terminate(self):
        self.audio.terminate()

    def clear_tracks(self):
        """Delete all track files and reset track count."""
        print("Clearing all tracks...")
        for file in os.listdir('.'):
            if file.startswith('track_') and file.endswith('.wav'):
                try:
                    os.remove(file)
                    print(f"Deleted {file}")
                except Exception as e:
                    print(f"Error deleting file {file}: {e}")
        self.track_count = 0
        print("All tracks cleared.")

def main():
    recorder = AudioRecorder()

    print("Press 'r' to start recording, 's' to stop and save, 'q' to quit.")
    while True:
        if keyboard.is_pressed('r'):  # Start recording
            recorder.start_recording()
            while keyboard.is_pressed('r'):  # Prevent multiple triggers
                pass
        elif keyboard.is_pressed('s'):  # Stop and save
            recorder.stop_recording()
            while keyboard.is_pressed('s'):  # Prevent multiple triggers
                pass
        elif keyboard.is_pressed('c'):  # Clear tracks
            if recorder.recording:
                recorder.stop_recording()
            recorder.clear_tracks()
            print("Program restarted. Press 'r' to start recording.")
            while keyboard.is_pressed('c'):
                pass
        elif keyboard.is_pressed('q'):  # Quit
            if recorder.recording:
                recorder.stop_recording()
            recorder.terminate()
            print("Application exited.")
            break

if __name__ == "__main__":
    main()




