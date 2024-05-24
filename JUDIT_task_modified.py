from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']

import psutil
# Set the priority of the process to high to ensure the experiment runs smoothly without interruptions
p = psutil.Process()
p.nice(psutil.HIGH_PRIORITY_CLASS)

# Import various PsychoPy modules needed for the experiment setup and execution
from psychopy import visual, core, event, sound, gui, data, monitors
import datetime
import os
import numpy as np
import pandas as pd
import random
import csv
from tqdm import tqdm

# Define constants used throughout the experiment
TODAY = datetime.datetime.now().strftime('%d-%m-%Y')
BASE_FREQ = 523.25  # Base frequency for tone generation in Hz
DURATION = 0.08  # Duration of each tone in seconds
INTENSITY_NORMAL_DB = -6  # Default sound intensity in decibels
SAMPLE_RATE = 48000  # Sampling rate for the audio in Hz
FIXATION_TIME = 1  # Duration for fixation cross display in seconds
SEQ_LEN = 14  # Number of tones in a sequence
NUM_BLOCKS = 6  # Number of experimental blocks

# Monitor configuration for consistent display
monitor_name = 'defaultMonitor'
monitor_width = 53.0  # Monitor width in centimeters
monitor_distance = 60.0  # Viewing distance in centimeters
monitor_resolution = [1920, 1080]  # Resolution of the monitor
mon = monitors.Monitor(monitor_name)
mon.setWidth(monitor_width)
mon.setDistance(monitor_distance)
mon.setSizePix(monitor_resolution)

# Create a dialogue box to collect participant number and whether to skip practice
dialogue = gui.Dlg(title="JUDIT")
dialogue.addField('Participant number:')
dialogue.addField('Skip practice phase?', initial=False)
dialogue.show()
participant_number = dialogue.data[0]
skip_practice = bool(dialogue.data[1])

# Create a window for displaying the experiment
win = visual.Window(monitor=mon, fullscr=True, color=(-0.1, -0.1, -0.1))
fixation = visual.TextStim(win, text='+', height=0.1, color=(1, 1, 1))
message = visual.TextStim(win, pos=(0, -0.3), height=0.05)
mouse = event.Mouse(win=win)
mouse.setVisible(False)

# Experiment instructions displayed at the start
instructions_text = """
Welcome to the experiment. \n\n
In this task, you will hear a series of tones. You need to decide if any of the tones differed in intensity from the others.
Press 'y' for Yes if you think there was a different tone, and 'n' for No if you think all tones were the same.\n\n
Press the space bar to continue."""
instructions = visual.TextStim(win, text=instructions_text, pos=(0, 0), wrapWidth=1.5)

# Prepare directory for saving data
data_dir = 'data/'
os.makedirs(data_dir, exist_ok=True)

# Function to display instructions and wait for space bar press
def show_instructions():
    instructions.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

# Convert dB value to amplitude
def db_to_amplitude(db):
    return 10 ** (db / 20)

# Generate a single tone with specified parameters
def generate_tone(frequency, duration, sample_rate, db):
    amplitude = db_to_amplitude(db)
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    attack_duration = int(sample_rate * 0.02)
    release_duration = int(sample_rate * 0.02)
    envelope = np.ones_like(tone)
    envelope[:attack_duration] = np.linspace(0, 1, attack_duration)
    envelope[-release_duration:] = np.linspace(1, 0, release_duration)
    tone = tone * envelope
    return tone

# Combine individual tones into a sequence with specified intervals
def combine_tones(sequence, sample_rate):
    combined_tone = np.array([], dtype=np.float32)
    for tone, interval in sequence:
        silence = np.zeros(int(sample_rate * interval), dtype=np.float32)
        combined_tone = np.concatenate((combined_tone, tone, silence))
    return combined_tone

# Load trial structure from CSV files in a directory
def load_trial_structure():
    trial_list_path = "trialList/"
    structure_files = [f for f in os.listdir(trial_list_path) if f.startswith("JUDIT")]
    chosen_filename = random.choice(structure_files)
    trial_data = pd.read_csv(trial_list_path + chosen_filename)
    structure_number = chosen_filename.split('_')[-1].split('.')[0]
    return trial_data, structure_number

# Run a single trial based on provided trial data
def run_trial(trial_data, practice=False, intensity_change_db=3):
    trial_num = int(trial_data['trial_num'])  # Extract trial number
    periodic = trial_data['periodic']  # Whether the tones are periodic
    has_high_intensity = trial_data['has_high_intensity']  # If there is a tone with higher intensity
    chosen_IOI = float(trial_data['chosen_IOI']) if trial_data['chosen_IOI'] else None  # Inter-onset interval
    high_intensity_index = int(trial_data['high_intensity_index']) if not pd.isna(trial_data['high_intensity_index']) else None  # Index of the high intensity tone
    intervals = eval(trial_data['intervals'])  # Time intervals between tones

    # Generate the sequence of tones for the trial
    sequence = []
    for i in range(SEQ_LEN):
        interval = intervals[i]
        db = INTENSITY_NORMAL_DB + intensity_change_db if i == high_intensity_index else INTENSITY_NORMAL_DB
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, db)
        sequence.append((tone, interval))

    combined_tone = combine_tones(sequence, SAMPLE_RATE)
    fixation.draw()  # Display fixation cross
    win.flip()
    core.wait(FIXATION_TIME)  # Wait for a fixed amount of time

    # Play the combined tone sequence
    tone_obj = sound.Sound(combined_tone, sampleRate=SAMPLE_RATE)
    tone_obj.play()
    core.wait(tone_obj.getDuration())  # Wait until tone playback is complete
    tone_obj.stop()  # Stop the tone playback

    # Collect user response
    response_clock = core.Clock()
    message.setText("""Was there a louder tone?\n\nYes (y)     /     No (n)""")
    message.setPos((0, 0))
    message.setHeight(0.1)
    message.draw()
    win.flip()
    response_clock.reset()
    keys = event.waitKeys(keyList=['y', 'n', 'escape'], timeStamped=response_clock)
    if 'escape' in [key[0] for key in keys]:
        win.close()
        core.quit()  # Exit if escape is pressed

    user_response = 'yes' if 'y' in keys[0][0] else 'no'
    response_time = round(keys[0][1], 3)
    correct_answer = 'yes' if has_high_intensity else 'no'
    correct = 1 if user_response == correct_answer else 0
    periodic = 1 if periodic==True else 0
    hasManip = 1 if has_high_intensity else 0

    # Save response data if not in practice mode
    if not practice:
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([participant_number, periodic, chosen_IOI, hasManip, trial_num, high_intensity_index, user_response, correct_answer, correct, response_time])
    
    return user_response, correct_answer, correct, response_time

# Parameters and functions for adaptive tracking
initial_intensity_change_db = 3  # Initial intensity change in dB for adaptive tracking
min_intensity_change_db = 0.125  # Minimum intensity change
max_intensity_change_db = 6  # Maximum intensity change
step_size_db = 0.125  # Step size for adjusting intensity change
correct_responses = 0  # Counter for correct responses
incorrect_responses = 0  # Counter for incorrect responses
current_intensity_change_db = initial_intensity_change_db  # Current intensity change
adaptive_trials = 32  # Number of adaptive trials
adaptive_tracking_data = []  # List to store data from adaptive trials
last_three_trials = []  # List to store intensities of the last three trials

# Function to run an adaptive trial and adjust intensity based on user response
def run_adaptive_trial(trial_num):
    global correct_responses, incorrect_responses, current_intensity_change_db
    sequence = []
    intervals = [0.15] * SEQ_LEN  # Set consistent intervals between tones for simplicity

    # Randomly choose one tone to have higher intensity
    high_intensity_index = random.randint(1, SEQ_LEN - 2)
    for i in range(SEQ_LEN):
        db = INTENSITY_NORMAL_DB
        if i == high_intensity_index:
            db += current_intensity_change_db
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, db)
        sequence.append((tone, intervals[i]))

    combined_tone = combine_tones(sequence, SAMPLE_RATE)
    fixation.draw()
    win.flip()
    core.wait(FIXATION_TIME)
    
    # Play the tone sequence
    tone_obj = sound.Sound(combined_tone, sampleRate=SAMPLE_RATE)
    tone_obj.play()
    core.wait(tone_obj.getDuration())
    tone_obj.stop()

    # Collect user response
    response_clock = core.Clock()
    message.setText("""Was there a louder tone?\n\nYes (y)     /     No (n)""")
    message.setPos((0, 0))
    message.setHeight(0.1)
    message.draw()
    win.flip()
    response_clock.reset()
    keys = event.waitKeys(keyList=['y', 'n', 'escape'], timeStamped=response_clock)
    if 'escape' in [key[0] for key in keys]:
        win.close()
        core.quit()

    user_response = 'yes' if 'y' in keys[0][0] else 'no'
    response_time = round(keys[0][1], 3)
    correct_answer = 'yes'
    correct = 1 if user_response == correct_answer else 0

    # Store adaptive tracking data
    adaptive_tracking_data.append([trial_num, current_intensity_change_db, user_response, correct])

    # Adjust intensity based on responses to find the threshold
    if correct:
        correct_responses += 1
        incorrect_responses = 0
        if correct_responses >= 1:
            current_intensity_change_db = max(min_intensity_change_db, current_intensity_change_db - step_size_db)
            correct_responses = 0
    else:
        incorrect_responses += 1
        if incorrect_responses >= 2:
            current_intensity_change_db = min(max_intensity_change_db, current_intensity_change_db + step_size_db)
            incorrect_responses = 0

    # Store the last three trials' intensities to calculate the moving average
    last_three_trials.append(current_intensity_change_db)
    if len(last_three_trials) > 3:
        last_three_trials.pop(0)

    # Return the average of the last three trials
    return sum(last_three_trials) / len(last_three_trials)

# Run practice trials with adaptive intensity adjustment
def run_adaptive_practice():
    practice_instructions_text = """This is a practice phase.\n
    You will hear a series of tones and need to decide if any of them differed in intensity.
    Press 'y' for Yes and 'n' for No.\n
    Press the space bar to begin."""
    practice_instructions = visual.TextStim(win, text=practice_instructions_text, pos=(0, 0), wrapWidth=1.5)
    practice_instructions.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    for trial_num in tqdm(range(adaptive_trials), desc="Adaptive Practice Trials"):
        current_intensity_change_db = run_adaptive_trial(trial_num)

    # Inform participant of their intensity change threshold at the end of practice (for debugging purposes)
    end_practice_text = f"""Practice phase complete.\n\n
    Your 50% threshold intensity change is {current_intensity_change_db:.2f} dB.\n
    Press the space bar to begin the main experiment."""
    end_practice = visual.TextStim(win, text=end_practice_text, pos=(0, 0), wrapWidth=1.5)
    end_practice.draw() 
    win.flip()
    event.waitKeys(keyList=['space'])

    # Save adaptive tracking data to file
    adaptive_tracking_filename = f"{data_dir}adaptive_tracking_{participant_number}_{TODAY}.csv"
    with open(adaptive_tracking_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['trial_num', 'intensity_change_db', 'user_response', 'correct'])
        writer.writerows(adaptive_tracking_data)

    return current_intensity_change_db

# Main experiment function
def main():
    show_instructions()
    trial_data, structure_number = load_trial_structure()
    global filename
    filename = f"{data_dir}JUDIT_{participant_number}_{structure_number}_{TODAY}.csv"
    TRIALS_PER_BLOCK = len(trial_data) // NUM_BLOCKS
    block_num = 0
    block_trials = trial_data[:TRIALS_PER_BLOCK]
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['participant_number', 'periodic', 'chosen_IOI', 'has_high_intensity', 'trial_num', 'high_intensity_index', 'user_response', 'correct_answer', 'correct', 'response_time'])
    if not skip_practice:
        adaptive_intensity_change_db = run_adaptive_practice()
    try:
        for index, trial in tqdm(block_trials.iterrows(), total=len(block_trials), desc=f"Block {block_num + 1} Trials"):
            run_trial(trial, intensity_change_db=adaptive_intensity_change_db)
        block_num += 1
        while block_num < NUM_BLOCKS:
            block_trials = trial_data[block_num * TRIALS_PER_BLOCK: (block_num + 1) * TRIALS_PER_BLOCK]
            break_text = f"Block {block_num} complete. Take a short break.\nPress the space bar to continue."
            break_message = visual.TextStim(win, text=break_text, pos=(0, 0), wrapWidth=1.5)
            break_message.draw()
            win.flip()
            event.waitKeys(keyList=['space'])
            for index, trial in tqdm(block_trials.iterrows(), total=len(block_trials), desc=f"Block {block_num + 1} Trials"):
                run_trial(trial, intensity_change_db=adaptive_intensity_change_db)
            block_num += 1
    finally:
        mouse.setVisible(True)
        win.close()

if __name__ == "__main__":
    main()
