import pyaudio
import wave
import threading
import keyboard  
import numpy as np  
import os 
import pygame 
import scipy 

# settings / presets
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
GAIN = 5.0  


# audio recorder class
# handles recording, playback, and visualization
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


    # recording 
    # starts recording audio and applies gain
    def start_recording(self):
        if self.recording:
            print("Already recording!")
            return

        self.stream = self.audio.open(format=FORMAT, channels=CHANNELS,
                                      rate=RATE, input=True,
                                      frames_per_buffer=CHUNK)
        self.frames = []
        self.recording = True
        print(f"Recording started. Press 'S' to stop and save, 'Q' to quit.")
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


    # very faint when testing audio - applied gain to audio data
    def apply_gain(self, data):
        try:
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplified_data = np.clip(audio_data * GAIN, -32768, 32767).astype(np.int16)
            return amplified_data.tobytes()
        except Exception as e:
            print(f"Error applying gain: {e}")
            return data  


    # stop recording 
    # saves file after recording is stopped
    # automatically plays the latest track after saving 
    # simultaneously layers all tracks on top of each other
    # and plays them in a loop
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
            # visualize the latest track with kaleidoscope
            self.visualize_kaleidoscope(latest_track)
            
        self.play_tracks() 


    # save the file as a new wav file in the current directory
    # save tracks as track_1.wav, track_2.wav, etc.
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
    

    # play recorded tracks in a loop
    def play_tracks(self):        
        self.playing = True
        print("Playing tracks on loop...")
        for track in self.tracks:
            threading.Thread(target=self.play_track, args=(track,)).start()
    

    # play a single track 
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
    

    # stop playback
    # stops playback of all tracks
    def stop_playback(self):
        if not self.playing:
            print("Not currently playing tracks!")
            return

        self.playing = False
        print("Playback stopped.")
    

    # terminate audio stream
    def terminate(self):
        self.audio.terminate()
    

    # loop tracks
    # play all tracks in a loop
    # called when the user presses 'p' to play tracks
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
    

    # clear tracks
    # delete all track files and reset track count
    # called when the user presses 'c' to clear tracks
    # need to press 'c' twice to clear tracks 
    def clear_tracks(self):
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
    

    # used to visualize the audio file with dynamic patterns, colors, and visuals using FFT and Pygame
    # uses FFT to analyze the audio signal and create a kaleidoscope effect
    # with dynamic patterns and colors based on the audio frequency spectrum
    # creates a kaleidoscope effect with dynamic patterns and colors based on the audio frequency spectrum
    def visualize_kaleidoscope(self, filename):
        import scipy.ndimage

        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Dynamic Kaleidoscope Visualization")
        clock = pygame.time.Clock()

        # read audio input
        with wave.open(filename, 'rb') as wf:
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            audio_signal = np.frombuffer(audio_data, dtype=np.int16)

        # normalize audio 
        audio_signal = audio_signal / np.max(np.abs(audio_signal))

        # start audio playback in separate thread
        threading.Thread(target=self.play_track, args=(filename,), daemon=True).start()

        # kaleidoscope parameters
        size = 100  
        base_image = np.random.rand(size, size, 3) * 255  
        base_image = base_image.astype(np.uint8)

        running = True
        frame = 0  
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # clear screen
            screen.fill((0, 0, 0))

            # create FFT from the audio signal
            chunk_size = 100  
            start = (frame * chunk_size) % len(audio_signal)
            end = start + chunk_size
            audio_chunk = audio_signal[start:end]

            if len(audio_chunk) > 0:
                # perform fft
                # get magnitude 
                fft_result = np.fft.fft(audio_chunk)
                fft_magnitude = np.abs(fft_result[:len(fft_result) // 2])  
                # normalize 
                fft_magnitude = fft_magnitude / np.max(fft_magnitude) 

                # split fft into frequency bands
                # low frequencies 
                low_band = np.mean(fft_magnitude[:len(fft_magnitude) // 3])  
                # mid frequencies 
                mid_band = np.mean(fft_magnitude[len(fft_magnitude) // 3:2 * len(fft_magnitude) // 3]) 
                # high frequencies
                high_band = np.mean(fft_magnitude[2 * len(fft_magnitude) // 3:])  

                # map frequency to visual parameters
                # map to kaleidoscope parameters
                # rotate based on mid frequencies
                rotation_angle = int(mid_band * 360)  
                # scale based on low frequencies
                scale_factor = 1 + low_band * 2  
                # color based on high frequencies
                color_shift = (int(high_band * 255), int(mid_band * 255), int(low_band * 255))  

                # rotate and scale 
                rotated_image = scipy.ndimage.rotate(base_image, rotation_angle, reshape=False)  
                scaled_image = scipy.ndimage.zoom(rotated_image, (scale_factor, scale_factor, 1), order=1)  
                scaled_image = scaled_image[:size, :size, :] 

                # create symmetry
                # create mirrored image
                mirrored_image = np.concatenate((scaled_image, scaled_image[:, ::-1, :]), axis=1)
                mirrored_image = np.concatenate((mirrored_image, mirrored_image[::-1, :, :]), axis=0)

                # color shift
                mirrored_image = (mirrored_image + np.array(color_shift)) % 255
                mirrored_image = mirrored_image.astype(np.uint8)

                # radial patterns
                # created with sine waves
                for i in range(0, size, 10):
                    pygame.draw.circle(screen, color_shift, (400, 300), int(i * mid_band), 1)

                # display 
                surface = pygame.surfarray.make_surface(mirrored_image)
                screen.blit(pygame.transform.scale(surface, (800, 600)), (0, 0))

            # update display
            pygame.display.flip()
            clock.tick(60)
            frame += 1

        pygame.quit()


def main():
    recorder = AudioRecorder()

    print("Press 'r' to start recording, 's' to stop and save, press 'c' twice to clear tracks, and 'q' to quit.")
    while True:
        # start recording when 'r' is pressed
        if keyboard.is_pressed('r'): 
            recorder.start_recording()
            # prevent multiple triggers
            while keyboard.is_pressed('r'): 
                pass
        # stop recording and save
        elif keyboard.is_pressed('s'): 
            recorder.stop_recording()
            # prevent multiple triggers
            while keyboard.is_pressed('s'): 
                pass
        # play tracks when 'p' is pressed
        elif keyboard.is_pressed('p'): 
            recorder.play_tracks()
            # prevent multiple triggers
            while keyboard.is_pressed('p'): 
                pass
        # clear tracks when 'c' is pressed
        elif keyboard.is_pressed('c'): 
            if recorder.recording:
                recorder.stop_recording()
            recorder.clear_tracks()
            print("Program restarted. Press 'r' to start recording.")
            # prevent multiple triggers
            while keyboard.is_pressed('c'):
                pass
        # quit the application when 'q' is pressed
        elif keyboard.is_pressed('q'): 
            if recorder.recording:
                recorder.stop_recording()
            recorder.terminate()
            print("Application exited.")
            break

if __name__ == "__main__":
    main()




