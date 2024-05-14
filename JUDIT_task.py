from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']

import psutil
p = psutil.Process()
p.nice(psutil.HIGH_PRIORITY_CLASS)

from psychopy import visual, core, event, sound, gui, data, monitors
import os
import numpy as np
import pandas as pd
import random
import csv

# Constants
BASE_FREQ = 523.25  # Hz
DURATION = 0.08  # seconds
INTENSITY_NORMAL = 0.5  # normalized intensity
SAMPLE_RATE = 96000  # Hz
FIXATION_TIME = 1  # seconds for fixation cross
SEQ_LEN = 14
PRACTICE_TRIALS = 8  # number of practice trials

# Monitor specifications
monitor_name = 'defaultMonitor'
monitor_width = 53.0  # Width of the monitor in cm
monitor_distance = 60.0  # Distance from the monitor in cm
monitor_resolution = [1920, 1080]  # Screen resolution

# Create a Monitor object
mon = monitors.Monitor(monitor_name)
mon.setWidth(monitor_width)
mon.setDistance(monitor_distance)
mon.setSizePix(monitor_resolution)

# Participant info dialogue
dialogue = gui.Dlg(title="JUDIT")
dialogue.addField('Participant number:')
dialogue.addField('Condition (1 - 3):')
dialogue.addField('Skip practice phase?', initial=False)
dialogue.show()

participant_number = dialogue.data[0]
condition = int(dialogue.data[1])
skip_practice = bool(dialogue.data[2])

# Initialize PsychoPy window and stimuli
win = visual.Window(monitor=mon, fullscr=True, color=(-0.1, -0.1, -0.1))
fixation = visual.TextStim(win, text='+', height=0.1, color=(1, 1, 1))
message = visual.TextStim(win, pos=(0, -0.3), height=0.05)
mouse = event.Mouse(win=win)
mouse.setVisible(False)

# Conditions as prose
conditions = {1: 'Easy', 2: 'Medium', 3: 'Hard'}[condition]

# Instructions screen
instructions_text = """Welcome to the experiment.
In this task, you will hear a series of tones. You need to decide if any of the tones differed in intensity from the others.
Press 'y' for Yes if you think there was a different tone, and 'n' for No if you think all tones were the same.
Press the space bar to continue."""
instructions = visual.TextStim(win, text=instructions_text, pos=(0, 0), wrapWidth=1.5)

# Show instructions
def show_instructions():
    instructions.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

# Data file setup
data_dir = 'data/'
os.makedirs(data_dir, exist_ok=True)

# Generate tone
def generate_tone(frequency, duration, sample_rate, amplitude):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Apply envelope
    attack_duration = int(sample_rate * 0.02)
    release_duration = int(sample_rate * 0.02)
    envelope = np.ones_like(tone)
    envelope[:attack_duration] = np.linspace(0, 1, attack_duration)
    envelope[-release_duration:] = np.linspace(1, 0, release_duration)
    
    tone = tone * envelope
    
    return tone

# Combine tones into one continuous sound
def combine_tones(sequence, sample_rate):
    combined_tone = np.array([], dtype=np.float32)
    for tone, interval in sequence:
        silence = np.zeros(int(sample_rate * interval), dtype=np.float32)
        combined_tone = np.concatenate((combined_tone, tone, silence))
    return combined_tone

# Load pre-generated trial structure
def load_trial_structure(condition):
    """
    Load the pre-generated trial structure for a given condition.
    """
    trial_list_path = "trialList/"
    structure_files = [f for f in os.listdir(trial_list_path) if f.startswith(f"JUDIT_{condition}")]
    chosen_filename = random.choice(structure_files)
    trial_data = pd.read_csv(trial_list_path + chosen_filename)
    structure_number = chosen_filename.split('_')[-1].split('.')[0]
    print(type(trial_data))
    print(trial_data)

    return trial_data, structure_number

# Run trial
def run_trial(trial_data, practice=False):
    trial_num = int(trial_data['trial_num'])
    periodic = trial_data['periodic']
    has_high_intensity = trial_data['has_high_intensity']
    chosen_IOI = float(trial_data['chosen_IOI']) if trial_data['chosen_IOI'] else None
   # Instead of directly casting to int, check if it is NaN
    high_intensity_index = int(trial_data['high_intensity_index']) if not pd.isna(trial_data['high_intensity_index']) else None
    percentage_increase = float(trial_data['percentage_increase']) if trial_data['percentage_increase'] else None
    intervals = eval(trial_data['intervals'])

    sequence = []
    for i in range(SEQ_LEN):
        interval = intervals[i]
        amplitude = percentage_increase if i == high_intensity_index else INTENSITY_NORMAL
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, amplitude)
        sequence.append((tone, interval))

    combined_tone = combine_tones(sequence, SAMPLE_RATE)
    
    # Display fixation cross
    fixation.draw()
    win.flip()
    core.wait(FIXATION_TIME)

    # Play combined tone and record duration
    tone_obj = sound.Sound(combined_tone, sampleRate=SAMPLE_RATE)
    tone_obj.play()
    core.wait(tone_obj.getDuration())
    tone_obj.stop()  # Ensure the tone is stopped
    
    # Collect response
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
    correct_answer = 'yes' if has_high_intensity else 'no'
    correct = 1 if user_response == correct_answer else 0
    periodic = 1 if periodic==True else 0
    hasManip = 1 if has_high_intensity else 0

    if not practice:
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([participant_number, condition, periodic, chosen_IOI, hasManip, trial_num, high_intensity_index, user_response, correct_answer, correct, response_time, percentage_increase])

    return user_response, correct_answer, correct, response_time

# Run practice
def run_practice():
    # Path to the practice trials file
    practice_file_path = "trialList/prac_file.csv"
    
    # Load practice trials
    practice_trials = pd.read_csv(practice_file_path)
    
    practice_instructions_text = """This is a practice phase.
    You will hear a series of tones and need to decide if any of them differed in intensity.
    Press 'y' for Yes and 'n' for No.
    Press the space bar to begin."""
    practice_instructions = visual.TextStim(win, text=practice_instructions_text, pos=(0, 0), wrapWidth=1.5)
    practice_instructions.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    # Run each practice trial
    for index, trial in practice_trials.iterrows():
        run_trial(trial, practice=True)

    end_practice_text = """Practice phase complete.
    Press the space bar to begin the main experiment."""
    end_practice = visual.TextStim(win, text=end_practice_text, pos=(0, 0), wrapWidth=1.5)
    end_practice.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

# Main function
def main():
    show_instructions()
    
    # Load main trials, not including practice trials
    trial_data, structure_number = load_trial_structure(condition)
    
    global filename
    filename = f"{data_dir}JUDIT_{participant_number}_{condition}_{structure_number}.csv"
    
    # Write header for the trial results file
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['participant_number', 'condition', 'periodic', 'chosen_IOI', 'has_high_intensity', 'trial_num', 'high_intensity_index', 'user_response', 'correct_answer', 'correct', 'response_time', 'percentage_increase'])

    # Run practice if not skipped
    if not skip_practice:
        run_practice()
    
    try:
        # Iterate through each row in the DataFrame, ensuring it's treated as a single trial
        for index, trial in trial_data.iterrows():
            run_trial(trial)
    finally:
        mouse.setVisible(True)
        win.close()


# Run the experiment
if __name__ == "__main__":
    main()
