#!/usr/bin/env python3
# Test script to verify audio system

import pygame
import os
import time

# Initialize pygame and mixer FIRST
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
print("✓ Pygame and mixer initialized")

# Now import audio manager
from amthanh import quan_ly_am_thanh

print("\n=== Testing Audio System ===\n")

# Test 1: Check if sounds were discovered
print("1. Kiểm tra file âm thanh được phát hiện:")
if quan_ly_am_thanh.sounds:
    for key, path in quan_ly_am_thanh.sounds.items():
        print(f"   {key}: {path}")
else:
    print("   ✗ Không tìm thấy file âm thanh!")

# Test 2: Play background music
print("\n2. Phát nhạc nền (5 giây):")
quan_ly_am_thanh.play_nhac_nen()
time.sleep(5)
quan_ly_am_thanh.stop_music()
print("   ✓ Hoàn thành")

# Test 3: Play boss music
print("\n3. Phát nhạc boss (5 giây):")
quan_ly_am_thanh.play_nhac_boss()
time.sleep(5)
quan_ly_am_thanh.stop_music()
print("   ✓ Hoàn thành")

# Test 4: Play shooting sound
print("\n4. Phát âm thanh bắn súng 3 lần:")
for i in range(3):
    quan_ly_am_thanh.play_tien_sung()
    time.sleep(0.5)
print("   ✓ Hoàn thành")

# Test 5: Play item pickup sound
print("\n5. Phát âm thanh nhặt item 2 lần:")
for i in range(2):
    quan_ly_am_thanh.play_nhat_item()
    time.sleep(0.5)
print("   ✓ Hoàn thành")

print("\n=== Kết thúc test ===")
