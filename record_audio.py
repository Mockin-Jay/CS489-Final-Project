import pyaudio
import wave
import threading
import keyboard  
import time
import numpy as np  
import os 
import pygame 
import scipy 

# Audio recording settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
GAIN = 5.0  

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.recording = False
        self.lock = threading.Lock()
        self.track_count = 0
        self.tracks = []
        self.playing = False

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
            return data  

    def stop_recording(self):
        if not self.recording:
            print("Not currently recording!")
            return

        self.recording = False
        self.stream.stop_stream()
        self.stream.close()
        print("Recording stopped. Saving file...")
        self.save_file()

        if self.tracks:
            latest_track = self.tracks[-1]
            print(f"Playing the latest track: {latest_track}")
            self.visualize_kaleidoscope(latest_track)
            
        self.play_tracks() 

    def save_file(self):
        self.track_count += 1
        filename = f"track_{self.track_count}.wav"
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(self.frames))
            self.tracks.append(filename)
            print(f"File saved as {filename}")
        except Exception as e:
            print(f"Error saving file: {e}")
    
    def play_tracks(self):
        """Play all recorded tracks in a loop."""
        """if self.playing:
            print("Already playing tracks!")
            return"""
        
        self.playing = True
        print("Playing tracks on loop...")
        for track in self.tracks:
            threading.Thread(target=self.play_track, args=(track,)).start()
    
    def play_track(self, track):
        while self.playing:
            try:
                with wave.open(track, 'rb') as wf:
                    stream = self.audio.open(format=self.audio.get_format_from_width(wf.getsampwidth()),
                                             channels=wf.getnchannels(),
                                             rate=wf.getframerate(),
                                             output=True)
                    data = wf.readframes(CHUNK)
                    while data and self.playing:
                        stream.write(data)
                        data = wf.readframes(CHUNK)
                    stream.close()
            except Exception as e:
                print(f"Error playing track {track}: {e}")
    
    def stop_playback(self):
        """Stop playback of tracks."""
        if not self.playing:
            print("Not currently playing tracks!")
            return

        self.playing = False
        print("Playback stopped.")
    
    def terminate(self):
        self.audio.terminate()
    
    def loop_tracks(self):
        while self.playing:
            for track in self.tracks:
                try:
                    with wave.open(track, 'rb') as wf:
                        stream = self.audio.open(format=self.audio.get_format_from_width(wf.getsampwidth()),
                                                channels=wf.getnchannels(),
                                                rate=wf.getframerate(),
                                                output=True)
                        data = wf.readframes(CHUNK)
                        while data and self.playing:
                            stream.write(data)
                            data = wf.readframes(CHUNK)
                        stream.close()
                except Exception as e:
                    print(f"Error playing track {track}: {e}")
    

    def clear_tracks(self):
        """Delete all track files and reset track count."""
        print("Clearing all tracks...")
        self.stop_playback()
        for file in os.listdir('.'):
            if file.startswith("track_") and file.endswith(".wav"):
                try:
                    os.remove(file)
                    print(f"Deleted {file}")
                except Exception as e:
                    print(f"Error deleting file {file}: {e}")
        for file in self.tracks:
            try:
                os.remove(file)
                print(f"Deleted {file}")
            except Exception as e:
                print(f"Error deleting file {file}: {e}")
        self.tracks = []
        self.track_count = 0
        print("All tracks cleared.")
    
    def visualize_kaleidoscope(self, filename):
        """Visualize the audio file with a dynamic kaleidoscope animation using FFT and Pygame."""
        import scipy.ndimage

        # Initialize Pygame
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Kaleidoscope Visualization with FFT")
        clock = pygame.time.Clock()

        # Read the audio file
        with wave.open(filename, 'rb') as wf:
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio_signal = np.frombuffer(audio_data, dtype=np.int16)

        # Normalize the audio signal
        audio_signal = audio_signal / np.max(np.abs(audio_signal))

        # Start audio playback in a separate thread
        threading.Thread(target=self.play_track, args=(filename,), daemon=True).start()

        # Kaleidoscope parameters
        size = 400  # Size of the kaleidoscope base image
        base_image = np.random.rand(size, size, 3) * 255  # Random RGB base image
        base_image = base_image.astype(np.uint8)

        running = True
        frame = 0  # Frame counter for animation
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            screen.fill((0, 0, 0))

            # Generate FFT from the audio signal
            chunk_size = 2048  # Number of audio samples to process per frame
            start = (frame * chunk_size) % len(audio_signal)
            end = start + chunk_size
            audio_chunk = audio_signal[start:end]

            if len(audio_chunk) > 0:
                # Perform FFT and get frequency magnitudes
                fft_result = np.fft.fft(audio_chunk)
                fft_magnitude = np.abs(fft_result[:len(fft_result) // 2])  # Take positive frequencies
                fft_magnitude = fft_magnitude / np.max(fft_magnitude)  # Normalize

                # Map FFT magnitudes to visual properties
                intensity = int(np.mean(fft_magnitude) * 255)  # Average intensity
                rotation_angle = int(np.sum(fft_magnitude * np.arange(len(fft_magnitude))) % 360)  # Weighted rotation
                color_shift = (intensity % 255, (intensity * 2) % 255, (intensity * 3) % 255)  # Dynamic color

                # Rotate and color-shift the base image
                rotated_image = scipy.ndimage.rotate(base_image, rotation_angle, reshape=False)  # Rotate image
                kaleidoscope_image = np.tile(rotated_image, (2, 2, 1))[:size, :size, :]  # Ensure 3D shape
                kaleidoscope_image = (kaleidoscope_image + np.array(color_shift)) % 255  # Apply color shift
                kaleidoscope_image = kaleidoscope_image.astype(np.uint8)

                # Create symmetry by mirroring the image
                mirrored_image = np.concatenate((kaleidoscope_image, kaleidoscope_image[:, ::-1, :]), axis=1)
                mirrored_image = np.concatenate((mirrored_image, mirrored_image[::-1, :, :]), axis=0)

                # Smooth the image using Gaussian blur
                smoothed_image = scipy.ndimage.gaussian_filter(mirrored_image, sigma=5)

                # Convert to Pygame surface and display
                surface = pygame.surfarray.make_surface(smoothed_image)
                screen.blit(pygame.transform.scale(surface, (800, 600)), (0, 0))

            # Update the display
            pygame.display.flip()
            clock.tick(60)
            frame += 1

        pygame.quit()


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
        elif keyboard.is_pressed('p'):  # Play tracks
            recorder.play_tracks()
            while keyboard.is_pressed('p'):  # Prevent multiple triggers
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




