import pygame
import os

class AudioManager:
    def __init__(self):
        # Initialize the mixer
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            
        self.volume = 0.5 
        self.music_file = None
        self.sounds = {} # Stores loaded Sound objects
        
        # Allocate channels (0=Music, 1-7=SFX)
        pygame.mixer.set_num_channels(8) 

    def load_music(self, filename):
        """Loads a music file from the assets folder."""
        path = os.path.join("audio", "assets", filename)
        if os.path.exists(path):
            try:
                pygame.mixer.music.load(path)
                self.music_file = path
            except Exception as e:
                print(f"Error loading music: {e}")
        else:
            print(f"Music file not found: {path}")

    def load_sfx(self, name, filename):
        """Loads a short sound effect into memory."""
        path = os.path.join("audio", "assets", filename)
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.volume)
                self.sounds[name] = sound
            except Exception as e:
                print(f"Error loading SFX {filename}: {e}")
        else:
            print(f"SFX file not found: {path}")

    def play_music(self, loop=True):
        """Plays the loaded music."""
        if self.music_file:
            loops = -1 if loop else 0
            pygame.mixer.music.play(loops)
            self.apply_volume()

    def play_sfx(self, name, loop=False):
        """Plays a loaded sound effect. Optional looping."""
        if name in self.sounds:
            loops = -1 if loop else 0
            # Play on an available channel
            self.sounds[name].play(loops)

    def stop_sfx(self, name):
        """Stops a specific sound effect immediately."""
        if name in self.sounds:
            self.sounds[name].stop()

    def change_volume(self, amount):
        """
        Adjusts volume by 'amount' (e.g., +0.05 or -0.05).
        Clamps between 0.0 and 1.0.
        """
        self.volume += amount
        self.volume = max(0.0, min(1.0, self.volume))
        self.apply_volume()
        return self.volume

    def apply_volume(self):
        """Sets the volume for Music and future SFX."""
        # 1. Set Music Volume
        pygame.mixer.music.set_volume(self.volume)
        
        # 2. Set SFX Volume (Update all loaded sounds)
        for s in self.sounds.values():
            s.set_volume(self.volume)