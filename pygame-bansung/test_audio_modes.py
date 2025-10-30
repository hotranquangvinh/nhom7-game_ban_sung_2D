#!/usr/bin/env python3
# Test script to verify audio system for different game modes

import pygame
import os
import time

# Initialize pygame and mixer FIRST
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
print("✓ Pygame and mixer initialized\n")

# Now import audio manager
from amthanh import quan_ly_am_thanh
from che_do import difficulty

print("=== Testing Audio Modes ===\n")

# Test 1: Normal mode
print("1. Che do binh thuong - Phat nhac nen (3 giay):")
difficulty.set_mode(difficulty.NORMAL)
quan_ly_am_thanh.stop_music()
quan_ly_am_thanh.play_nhac_nen()
time.sleep(3)
print("   ✓ Hoan thanh\n")

# Test 2: Boss arrives in normal mode
print("2. Che do binh thuong - Gap boss, phat nhac danh_boss (3 giay):")
quan_ly_am_thanh.stop_music()
quan_ly_am_thanh.play_nhac_boss()
time.sleep(3)
print("   ✓ Hoan thanh\n")

# Test 3: Hard mode
print("3. Che do kho - Phat nhac danh_boss tu dau (3 giay):")
difficulty.set_mode(difficulty.HARD)
quan_ly_am_thanh.stop_music()
quan_ly_am_thanh.play_nhac_boss()
time.sleep(3)
print("   ✓ Hoan thanh\n")

print("=== Ket thuc test ===")
