# Select audio backend
from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']

# Set high priority
import psutil
p = psutil.Process()
p.nice(psutil.HIGH_PRIORITY_CLASS)

# Import PsychoPy modules
from psychopy import visual, core, event, sound, gui, data

# Import other modules
import os
import numpy as np
import random
import csv

# Constants
BASE_FREQ = 523.25  # Hz
DURATION = 0.08  # seconds
INTENSITY_NORMAL = 0.5  # normalized intensity
SAMPLE_RATE = 96000  # Hz
FIXATION_TIME = 1  # seconds for fixation cross
TRIALS = 300  # number of trials
PRACTICE_TRIALS = 8  # number of practice trials
SEQ_LEN = 14

# Participant info dialogue
dialogue = gui.Dlg(title="JUDIT")
dialogue.addField('Participant number:')
dialogue.addField('Condition (1 - 3):')
dialogue.addField('Skip practice phase?', initial=False)
dialogue.show()

participant_number = dialogue.data[0]
condition = int(dialogue.data[1])
skip_practice = bool(dialogue.data[2])

# Define the amplitude ranges for each condition
amplitude_ranges = {
    1: (.75, .675),  # Easy
    2: (.675, .625),  # Medium
    3: (.575, .525)   # Hard
}

# Initialize PsychoPy window and stimuli
win = visual.Window([800, 600], fullscr=True, color=(-0.1, -0.1, -0.1))
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
filename = f"{data_dir}JUDIT_{conditions}_{participant_number}.csv"
structure_filename = f"{data_dir}JUDIT_{conditions}_{participant_number}_structure.csv"

# Write header for the trial structure file
with open(structure_filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['trial_num', 'periodic', 'chosen_IOI', 'has_high_intensity', 'high_intensity_index', 'percentage_increase', 'intervals'])

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

# Create sequence
def create_sequence(periodic, has_high_intensity, high_intensity_positions, condition):
    sequence = []
    high_intensity_index = None
    percentage_increase = None
    chosen_IOI = random.choice([0.2, 0.25]) if periodic else None
    intervals = []

    if has_high_intensity:
        high_intensity_index = high_intensity_positions.pop()
        amplitude_high = np.random.uniform(*amplitude_ranges[condition])
        percentage_increase = amplitude_high
    else:
        amplitude_high = INTENSITY_NORMAL

    for i in range(SEQ_LEN):
        interval = chosen_IOI if periodic else round(np.random.uniform(0.1, 0.375), 3)
        intervals.append(interval)
        amplitude = amplitude_high if i == high_intensity_index else INTENSITY_NORMAL
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, amplitude)
        sequence.append((tone, interval))
    
    return sequence, has_high_intensity, high_intensity_index, percentage_increase, chosen_IOI, intervals

# Combine tones into one continuous sound
def combine_tones(sequence, sample_rate):
    combined_tone = np.array([], dtype=np.float32)
    for tone, interval in sequence:
        silence = np.zeros(int(sample_rate * interval), dtype=np.float32)
        combined_tone = np.concatenate((combined_tone, tone, silence))
    return combined_tone

# Pre-generate and store sequences
def generate_and_store_sequences(trial_types, high_intensity_positions, condition):
    sequences = []
    for trial_num, (periodic, has_high_intensity) in enumerate(trial_types):
        sequence, has_high_intensity, high_intensity_index, percentage_increase, chosen_IOI, intervals = create_sequence(periodic, has_high_intensity, high_intensity_positions, condition)
        combined_tone = combine_tones(sequence, SAMPLE_RATE)
        trial_data = {
            'trial_num': trial_num,
            'sequence': sequence,
            'combined_tone': combined_tone,
            'periodic': periodic,
            'has_high_intensity': has_high_intensity,
            'high_intensity_index': high_intensity_index,
            'percentage_increase': percentage_increase,
            'chosen_IOI': chosen_IOI,
            'intervals': intervals
        }
        sequences.append(trial_data)

        # Write trial structure to the file
        with open(structure_filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([trial_num, periodic, chosen_IOI, has_high_intensity, high_intensity_index, percentage_increase, intervals])
    
    return sequences

# Run trial
def run_trial(trial_data, practice=False):
    trial_num = trial_data['trial_num']
    combined_tone = trial_data['combined_tone']
    sequence = trial_data['sequence']
    periodic = trial_data['periodic']
    has_high_intensity = trial_data['has_high_intensity']
    high_intensity_index = trial_data['high_intensity_index']
    percentage_increase = trial_data['percentage_increase']
    chosen_IOI = trial_data['chosen_IOI']
    
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
    periodic = 1 if chosen_IOI else 0
    hasManip = 1 if has_high_intensity else 0

    if not practice:
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([participant_number, condition, periodic, chosen_IOI, hasManip, trial_num, high_intensity_index, user_response, correct_answer, correct, response_time, percentage_increase])

    return user_response, correct_answer, correct, response_time

# Run practice
def run_practice(sequences):
    practice_instructions_text = """This is a practice phase.
    You will hear a series of tones and need to decide if any of them differed in intensity.
    Press 'y' for Yes and 'n' for No.
    Press the space bar to begin."""
    practice_instructions = visual.TextStim(win, text=practice_instructions_text, pos=(0, 0), wrapWidth=1.5)
    practice_instructions.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

    for trial_data in sequences:
        run_trial(trial_data, practice=True)

    end_practice_text = """Practice phase complete.
    Press the space bar to begin the main experiment."""
    end_practice = visual.TextStim(win, text=end_practice_text, pos=(0, 0), wrapWidth=1.5)
    end_practice.draw()
    win.flip()
    event.waitKeys(keyList=['space'])

# Main function
def main():
    show_instructions()
    
    trial_types = [(True, True), (True, False), (False, True), (False, False)] * (TRIALS // 4)
    random.shuffle(trial_types)
    high_intensity_positions = [11, 12, 13, 14] * (TRIALS // 4)
    random.shuffle(high_intensity_positions)

    if not skip_practice:
        practice_types = trial_types[:PRACTICE_TRIALS]
        practice_positions = high_intensity_positions[:PRACTICE_TRIALS]
        practice_sequences = generate_and_store_sequences(practice_types, practice_positions, condition)
        run_practice(practice_sequences)
    
    main_sequences = generate_and_store_sequences(trial_types, high_intensity_positions, condition)
    
    try:
        for trial_data in main_sequences:
            run_trial(trial_data)
    finally:
        mouse.setVisible(True)
        win.close()

# Run the experiment
main()
