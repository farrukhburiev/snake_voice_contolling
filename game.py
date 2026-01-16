import pygame
import random
import threading
import json
import queue
import os
import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# --- 1. SET YOUR WORKING DEVICE ID HERE ---
MY_MIC_DEVICE = 2  # <--- Change this to the number that worked in your test!

# --- CONFIGURATION ---
WIDTH, HEIGHT = 600, 400
SNAKE_SIZE = 20
FPS = 1 # Lowered slightly to make it easier to play by voice

# Colors
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)

# Global variables
current_direction = "RIGHT"
command_queue = queue.Queue()

# --- VOICE ENGINE ---
def voice_listener():
    global current_direction
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "model")
        model = Model(model_path) 
        rec = KaldiRecognizer(model, 16000)
        
        def callback(indata, frames, time, status):
            audio_data = (indata * 32768).astype(np.int16)
            command_queue.put(audio_data.tobytes())

        with sd.InputStream(samplerate=16000, device=MY_MIC_DEVICE, channels=1, callback=callback):
            print(f"--- VOICE CONTROL ACTIVE ---")
            while True:
                data = command_queue.get()
                
                # We check BOTH AcceptWaveform (finished) AND PartialResult (mid-word)
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    text = res.get("text", "")
                else:
                    partial = json.loads(rec.PartialResult())
                    text = partial.get("partial", "")

                if text:
                    # Logic to catch the word as soon as it appears in the text
                    if "up" in text or "top" in text:
                        if current_direction != "DOWN":
                            current_direction = "UP"
                            print(">>> ACTION: UP")
                            rec.Reset() # Clear the buffer so it doesn't repeat
                    elif "down" in text or "bottom" in text:
                        if current_direction != "UP":
                            current_direction = "DOWN"
                            print(">>> ACTION: DOWN")
                            rec.Reset()
                    elif "left" in text:
                        if current_direction != "RIGHT":
                            current_direction = "LEFT"
                            print(">>> ACTION: LEFT")
                            rec.Reset()
                    elif "right" in text:
                        if current_direction != "LEFT":
                            current_direction = "RIGHT"
                            print(">>> ACTION: RIGHT")
                            rec.Reset()

    except Exception as e:
        print(f"Voice Thread Error: {e}")
# --- GAME ENGINE ---
def run_game():
    global current_direction
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Voice Controlled Snake")
    clock = pygame.time.Clock()

    snake = [[100, 100], [80, 100], [60, 100]]
    food = [random.randrange(1, WIDTH//SNAKE_SIZE)*SNAKE_SIZE, 
            random.randrange(1, HEIGHT//SNAKE_SIZE)*SNAKE_SIZE]
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Move Snake logic
        head = list(snake[0])
        if current_direction == "UP": head[1] -= SNAKE_SIZE
        if current_direction == "DOWN": head[1] += SNAKE_SIZE
        if current_direction == "LEFT": head[0] -= SNAKE_SIZE
        if current_direction == "RIGHT": head[0] += SNAKE_SIZE

        snake.insert(0, head)

        # Eating Food
        if head == food:
            food = [random.randrange(1, WIDTH//SNAKE_SIZE)*SNAKE_SIZE, 
                    random.randrange(1, HEIGHT//SNAKE_SIZE)*SNAKE_SIZE]
        else:
            snake.pop()

        # Wall Collision
        if head[0] < 0 or head[0] >= WIDTH or head[1] < 0 or head[1] >= HEIGHT:
            print("Game Over: Hit the wall!")
            running = False
        
        # Self Collision
        if head in snake[1:]:
            print("Game Over: Hit yourself!")
            running = False

        # Drawing
        screen.fill(BLACK)
        for pos in snake:
            pygame.draw.rect(screen, GREEN, pygame.Rect(pos[0], pos[1], SNAKE_SIZE-2, SNAKE_SIZE-2))
        pygame.draw.rect(screen, RED, pygame.Rect(food[0], food[1], SNAKE_SIZE, SNAKE_SIZE))
        
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

# --- RUN EVERYTHING ---
if __name__ == "__main__":
    # Start the voice thread in the background
    threading.Thread(target=voice_listener, daemon=True).start()
    
    # Start the game in the main thread
    run_game()