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
TRIALS = 25 # number of trials

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
    writer.writerow(['p_num', 't_num', 'isPeriodic', 'resp', 'corAns', 'isCorrect', 'rt'])

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

def create_sequence(periodic=True):
    intervals = [0.2, 0.25] if periodic else [np.random.uniform(0.15, 0.35) for _ in range(7)]
    sequence = []
    high_intensity_index = None

    if random.random() < 0.5:
        high_intensity_index = random.choice([4, 5, 6])

    for i in range(7):
        amplitude = INTENSITY_HIGH if i == high_intensity_index else INTENSITY_NORMAL
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, amplitude)
        sequence.append((tone, intervals[i % len(intervals)]))
    
    return sequence, high_intensity_index is not None

def run_trial(trial_num, periodic):
    sequence, has_high_intensity = create_sequence(periodic)

    # Display fixation cross
    fixation.draw()
    win.flip()
    core.wait(FIXATION_TIME)

    # Play sequence
    for tone, interval in sequence:
        tone.play()
        core.wait(tone.getDuration() + interval)

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
    
    # Save data
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([participant_number, trial_num, periodic, user_response, correct_answer, correct, response_time])

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