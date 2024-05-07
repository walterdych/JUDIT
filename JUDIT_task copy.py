#####################################################
#
#                JUDIT Task
# (Judgment of Uneven Differential Intensity Tones)
#
#####################################################

# Import psychopy modules
from psychopy import visual, core, event, sound, gui, data

# Select audio backend
from psychopy import prefs
prefs.hardware['audioLib'] = ['PTB']

from psychopy.event import Mouse

# Import other modules
import numpy as np
import random
import csv

# Constants
BASE_FREQ = 440  # Hz
DURATION = 0.08  # seconds
INTENSITY_NORMAL = 0.5  # normalized intensity
SAMPLE_RATE = 48000  # Hz
FIXATION_TIME = 2  # seconds for fixation cross
TRIALS = 200 # number of trials

dialogue = gui.Dlg(title="JUDIT")
dialogue.addField('Participant number:')
dialogue.addField('Condition (1 - 3):')
dialogue.show()

participant_number = dialogue.data[0]
condition = int(dialogue.data[1])

# Define the amplitude ranges for each condition
amplitude_ranges = {
    1: (.75, .675),  # Easy
    2: (.675, .625),  # Medium
    3: (.575, .525)  # Hard
}

# Initialize PsychoPy window and stimuli
win = visual.Window([800, 600], fullscr=True, color=(-0.1, -0.1, -0.1))
fixation = visual.TextStim(win, text='+', height=0.1, color=(1, 1, 1))
message = visual.TextStim(win, pos=(0, -0.3), height=0.05)
mouse = Mouse(win=win)
mouse.setVisible(False)

# Conditions as prose
if condition == 1:
    conditions = 'Easy'
elif condition == 2:
    conditions = 'Medium'
elif condition == 3:
    conditions = 'Hard'

# Instructions screen
instructions = visual.TextStim(win, text="""Welcome to the experiment.
                               \n\nIn this task, you will hear a series of tones. You need to decide if any of the tones differed in intensity from the others.
                               \n\nPress 'y' for Yes if you think there was a different tone, and 'n' for No if you think all tones were the same.
                               \n\nPress the space bar to continue.""", pos=(0, 0), wrapWidth=1.5)

def show_instructions():
    instructions.draw()
    win.flip()
    event.waitKeys(keyList=['space'])  # Wait for space bar press to continue

# Data file setup
filename = f"data/JUDIT_{conditions}_{participant_number}.csv"
with open(filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['p_num', 'condition', 'isPeriodic', 'IOI', 'hasManip', 't_num', 'hasManip_idx', 'resp', 'corAns', 'isCorrect', 'rt', 'intAmnt', 'transTimes'])

def generate_tone(frequency, duration, sample_rate, amplitude):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)

    # Apply envelope (simple linear attack and release)
    attack_duration = int(sample_rate * 0.01)  # 10 ms attack
    release_duration = int(sample_rate * 0.01)  # 10 ms release
    envelope = np.ones_like(tone)

    # Create attack (linear ramp from 0 to 1)
    envelope[:attack_duration] = np.linspace(0, 1, attack_duration)
    
    # Create release (linear ramp from 1 to 0)
    envelope[-release_duration:] = np.linspace(1, 0, release_duration)

    # Ensure the tone is two-dimensional with shape (n_samples, n_channels)
    tone = tone * envelope
    if len(tone.shape) == 1:  # If tone is one-dimensional
        tone = tone.reshape(-1, 1)  # Reshape to two-dimensional (n_samples, 1)

    return sound.Sound(tone, sampleRate=sample_rate)

def create_sequence(periodic, has_high_intensity, high_intensity_positions, condition):
    sequence = []
    high_intensity_index = None
    percentage_increase = None
    chosen_IOI = None  # Variable to store the chosen IOI

    if has_high_intensity:
        high_intensity_index = high_intensity_positions.pop()
        # Select a random amplitude within the range for the condition
        amplitude_high = np.random.uniform(*amplitude_ranges[condition])
        percentage_increase = amplitude_high 
    else:
        amplitude_high = INTENSITY_NORMAL  # If there is no high intensity tone, use the normal amplitude

    for i in range(14):
        if periodic:
            chosen_IOI = random.choice([0.2, 0.25])  # Store the chosen IOI
            interval = chosen_IOI
        else:
            interval = np.random.uniform(0.1, 0.375)
            interval = round(interval, 3)  # Round to 3 decimal places
            

        amplitude = amplitude_high if i == high_intensity_index else INTENSITY_NORMAL
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, amplitude)  # Pass amplitude directly
        sequence.append((tone, interval))
    
    return sequence, has_high_intensity, high_intensity_index, percentage_increase, chosen_IOI  # Return the chosen IOI


def run_trial(trial_num, periodic, has_high_intensity, high_intensity_positions, condition):
    sequence, has_high_intensity, high_intensity_index, percentage_increase, chosen_IOI = create_sequence(periodic, has_high_intensity, high_intensity_positions, condition)

    # Display fixation cross
    fixation.draw()
    win.flip()

    # Play sequence and record transition times
    transition_clock = core.Clock()
    transition_times = []
    for tone, interval in sequence:
        tone.play()
        core.wait(tone.getDuration() + interval)
        transition_times.append(transition_clock.getTime())
        transition_clock.reset()

    # Setup response clock
    response_clock = core.Clock()  # Initialize the clock to track response time
    message.setText("""Was there a louder tone?
                        \n\nYes (y)     /     No (n)""")
    message.setPos((0, 0))  # Set position to the center of the screen
    message.setHeight(0.1)  # Set font size of message
    message.draw()
    win.flip()

    response_clock.reset()  # Start timing response as soon as the question is displayed
    keys = event.waitKeys(keyList=['y', 'n', 'escape'], timeStamped=response_clock)
    if 'escape' in [key[0] for key in keys]:
        win.close()
        core.quit()

    user_response = 'yes' if 'y' in keys[0][0] else 'no'
    response_time = keys[0][1]  # Get the time of the keypress

    correct_answer = 'yes' if has_high_intensity else 'no'
    correct = (user_response == correct_answer)
    # Make Binary
    correct = 1 if correct else 0
    periodic = 1 if periodic else 0
    hasManip = 1 if has_high_intensity else 0

    # Round transition times to 3 decimal places
    transition_times = [round(t, 3) for t in transition_times]
    response_time = round(response_time, 3)

    # Save
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([participant_number, condition, periodic, chosen_IOI, hasManip, trial_num, high_intensity_index, user_response, correct_answer, correct, response_time, percentage_increase, transition_times])

    return user_response, correct_answer, correct, response_time


def main():
    show_instructions()  # Display instructions before the trials begin
    try:
        # Create a list of trial types
        trial_types = [(True, True), (True, False), (False, True), (False, False)] * (TRIALS // 4)
        random.shuffle(trial_types)  # Randomize the order of trials

        # Create a list of possible positions for the high intensity tone and shuffle it
        high_intensity_positions = [11, 12, 13, 14] * (TRIALS // 4)
        random.shuffle(high_intensity_positions)

        for trial_num, (periodic, has_high_intensity) in enumerate(trial_types):
            run_trial(trial_num, periodic, has_high_intensity, high_intensity_positions, condition)
    finally:
        mouse.setVisible(True)
        win.close()

# Run the experiment
main()