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
prefs.hardware['audioLib'] = ['PTB', 'sounddevice', 'pyo', 'pygame']

from psychopy.event import Mouse

# Import other modules
import numpy as np
import random
import csv

# Constants
BASE_FREQ = 523.251  # Hz
DURATION = 0.08  # seconds
INTENSITY_NORMAL = 0.5  # normalized intensity
INTENSITY_HIGH = 0.65  # higher intensity
SAMPLE_RATE = 48000  # Hz
FIXATION_TIME = 2  # seconds for fixation cross
TRIALS = 200 # number of trials

# Setup the participant dialog box
info = {'Participant Number': ''}
dlg = gui.DlgFromDict(dictionary=info, title='Experiment Setup')
if dlg.OK == False:
    core.quit()  # user pressed cancel

participant_number = info['Participant Number']

# Initialize PsychoPy window and stimuli
win = visual.Window([800, 600], fullscr=True, color=(-0.1, -0.1, -0.1))
fixation = visual.TextStim(win, text='+', height=0.1, color=(1, 1, 1))
message = visual.TextStim(win, pos=(0, -0.3), height=0.05)
mouse = Mouse(win=win)
mouse.setVisible(False)


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
filename = f"JUDIT_{participant_number}.csv"
with open(filename, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['p_num', 't_num', 'isPeriodic', 'hasManip', 'hasManip_idx', 'resp', 'corAns', 'isCorrect', 'rt', 'transTimes'])

def generate_tone(frequency, duration, sample_rate, amplitude=1.0):
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

def create_sequence(periodic):
    sequence = []
    high_intensity_index = None

    if random.random() < 0.5:
        high_intensity_index = random.choice([11, 12, 13])

    for i in range(14):
        if periodic:
            interval = random.choice([0.2, 0.25])
        else:
            while True:
                interval = np.random.uniform(0.10, 0.45)
                interval = round(interval, 3)  # Round to 3 decimal places
                if interval not in [0.2, 0.25]:
                    break

        amplitude = INTENSITY_HIGH if i == high_intensity_index else INTENSITY_NORMAL
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, amplitude)
        sequence.append((tone, interval))
    
    return sequence, high_intensity_index

def run_trial(trial_num, periodic):
    sequence, has_high_intensity = create_sequence(periodic)

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

    # Save data
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([participant_number, trial_num, periodic, hasManip, has_high_intensity, user_response, correct_answer, correct, response_time, transition_times])

    return user_response, correct_answer, correct, response_time

def main():
    show_instructions()  # Display instructions before the trials begin
    try:
        for trial_num in range(TRIALS):  # number of trials
            periodic = random.choice([True, False])
            run_trial(trial_num, periodic)
    finally:
        mouse.setVisible(True)
        win.close()

if __name__ == "__main__":
    main()