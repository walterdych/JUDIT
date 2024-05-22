import os
import numpy as np
import random
import csv

# Constants
BASE_FREQ = 523.25  # Hz
DURATION = 0.08  # seconds
INTENSITY_NORMAL = 0.5  # normalized intensity
SAMPLE_RATE = 96000  # Hz
SEQ_LEN = 14
TRIALS = 192  # number of trials
NUM_STRUCTURES = 5  # number of different trial structures per condition
MANIP_POS = [11, 12, 13, 14]  # positions where high intensity is manipulated

# Function to generate tone
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

# Function to create sequence
def create_sequence(periodic, has_high_intensity, high_intensity_positions):
    sequence = []
    high_intensity_index = None
    chosen_IOI = random.choice([0.2, 0.25]) if periodic else None
    intervals = []

    if has_high_intensity:
        high_intensity_index = high_intensity_positions.pop()
    
    for i in range(SEQ_LEN):
        interval = chosen_IOI if periodic else round(np.random.uniform(0.1, 0.375), 3)
        intervals.append(interval)
        amplitude = INTENSITY_NORMAL
        tone = generate_tone(BASE_FREQ, DURATION, SAMPLE_RATE, amplitude)
        sequence.append((tone, interval))
    
    return sequence, has_high_intensity, high_intensity_index, chosen_IOI, intervals

# Function to combine tones into one continuous sound
def combine_tones(sequence, sample_rate):
    combined_tone = np.array([], dtype=np.float32)
    for tone, interval in sequence:
        silence = np.zeros(int(sample_rate * interval), dtype=np.float32)
        combined_tone = np.concatenate((combined_tone, tone, silence))
    return combined_tone

# Function to generate and store sequences
def generate_and_store_sequences(trial_types, high_intensity_positions, filename):
    sequences = []
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['trial_num', 'periodic', 'chosen_IOI', 'has_high_intensity', 'high_intensity_index', 'intervals'])
        for trial_num, (periodic, has_high_intensity) in enumerate(trial_types):
            sequence, has_high_intensity, high_intensity_index, chosen_IOI, intervals = create_sequence(periodic, has_high_intensity, high_intensity_positions)
            combined_tone = combine_tones(sequence, SAMPLE_RATE)
            trial_data = {
                'trial_num': trial_num,
                'sequence': sequence,
                'combined_tone': combined_tone,
                'periodic': periodic,
                'has_high_intensity': has_high_intensity,
                'high_intensity_index': high_intensity_index,
                'chosen_IOI': chosen_IOI,
                'intervals': intervals
            }
            sequences.append(trial_data)
            writer.writerow([trial_num, periodic, chosen_IOI, has_high_intensity, high_intensity_index, intervals])
    return sequences

# Generate multiple balanced trial structures and save them
for i in range(1, NUM_STRUCTURES + 1):
    trial_types = [(True, True), (True, False), (False, True), (False, False)] * (TRIALS // 4)
    random.shuffle(trial_types)
    high_intensity_positions = MANIP_POS * (TRIALS // len(MANIP_POS))
    random.shuffle(high_intensity_positions)
    filename = f"trialList/JUDIT_{i}.csv"
    generate_and_store_sequences(trial_types, high_intensity_positions, filename)
