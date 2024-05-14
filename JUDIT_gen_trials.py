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
TRIALS = 300  # number of trials
NUM_STRUCTURES = 5  # number of different trial structures per condition
MANIP_POS = [11, 12, 13, 14] # positions where high intensity is manipulated

# Define the amplitude ranges for each condition
amplitude_ranges = {
    1: (.75, .675),  # Easy
    2: (.675, .625),  # Medium
    3: (.575, .525)  # Hard
}

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

# Function to combine tones into one continuous sound
def combine_tones(sequence, sample_rate):
    combined_tone = np.array([], dtype=np.float32)
    for tone, interval in sequence:
        silence = np.zeros(int(sample_rate * interval), dtype=np.float32)
        combined_tone = np.concatenate((combined_tone, tone, silence))
    return combined_tone

# Function to generate and store sequences
def generate_and_store_sequences(trial_types, high_intensity_positions, condition, filename):
    sequences = []
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['trial_num', 'periodic', 'chosen_IOI', 'has_high_intensity', 'high_intensity_index', 'percentage_increase', 'intervals'])
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
            writer.writerow([trial_num, periodic, chosen_IOI, has_high_intensity, high_intensity_index, percentage_increase, intervals])
    return sequences

# Generate multiple balanced trial structures and save them
conditions = [1, 2, 3]
for condition in conditions:
    for i in range(1, NUM_STRUCTURES + 1):
        trial_types = [(True, True), (True, False), (False, True), (False, False)] * (TRIALS // 4)
        random.shuffle(trial_types)
        high_intensity_positions = MANIP_POS * (TRIALS // len(MANIP_POS))
        random.shuffle(high_intensity_positions)
        filename = f"trialList/JUDIT_{condition}_{i}.csv"
        generate_and_store_sequences(trial_types, high_intensity_positions, condition, filename)
