# test_audio.py - Kiểm tra hệ thống âm thanh
import pygame
import os

print("=" * 60)
print("KIỂM TRA HỆ THỐNG ÂM THANH")
print("=" * 60)

# Khởi tạo pygame
print("\n1. Khởi tạo pygame...")
pygame.init()
print("   ✓ pygame.init() OK")

# Khởi tạo mixer
print("\n2. Khởi tạo mixer...")
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    print("   ✓ pygame.mixer.init() OK")
except Exception as e:
    print(f"   ✗ Loi: {e}")

# Kiểm tra thư mục âm thanh
print("\n3. Kiểm tra thư mục âm thanh...")
am_thanh_folder = os.path.join('assets', 'am_thanh')
if os.path.exists(am_thanh_folder):
    print(f"   ✓ Thư mục tồn tại: {am_thanh_folder}")
    files = os.listdir(am_thanh_folder)
    print(f"   ✓ Tìm thấy {len(files)} file:")
    for f in files:
        size = os.path.getsize(os.path.join(am_thanh_folder, f))
        print(f"      - {f} ({size} bytes)")
else:
    print(f"   ✗ Thư mục không tồn tại: {am_thanh_folder}")

# Thử load âm thanh
print("\n4. Thử load các file âm thanh...")
sound_files = {
    'tien_sung': 'tieng_sung.mp3',
    'nhat_item': 'am_thanh_nhat_item.mp3',
    'that_bai': 'am_thanh_that_bai.mp3',
    'chuc_mung': 'am_thanh_chuc_mung_chien_thang.mp3',
    'boss': 'danh_boss.mp3',
    'nhac_nen': 'nhac_nen.mp3'
}

files_in_folder = {}
if os.path.exists(am_thanh_folder):
    for f in os.listdir(am_thanh_folder):
        files_in_folder[f.lower()] = os.path.join(am_thanh_folder, f)

for key, filename in sound_files.items():
    filename_lower = filename.lower()
    if filename_lower in files_in_folder:
        path = files_in_folder[filename_lower]
        try:
            if key in ['nhac_nen', 'boss', 'that_bai']:
                print(f"   ✓ {key}: {filename} (nhạc - sẽ load động)")
            else:
                sound = pygame.mixer.Sound(path)
                print(f"   ✓ {key}: {filename} ({sound.get_length():.2f}s)")
        except Exception as e:
            print(f"   ✗ {key}: {filename} - Loi: {e}")
    else:
        print(f"   ✗ {key}: {filename} - File không tìm thấy")

# Thử phát âm thanh
print("\n5. Thử phát nhạc nền...")
try:
    nhac_nen_path = files_in_folder.get('nhac_nen.mp3')
    if nhac_nen_path:
        pygame.mixer.music.load(nhac_nen_path)
        pygame.mixer.music.play(-1)
        print(f"   ✓ Nhạc đang phát: {nhac_nen_path}")
        print(f"   ✓ Đang phát: {pygame.mixer.music.get_busy()}")
        
        # Dừng sau khi kiểm tra
        pygame.mixer.music.stop()
        print("   ✓ Dừng nhạc thành công")
    else:
        print("   ✗ Không tìm thấy nhac_nen.mp3")
except Exception as e:
    print(f"   ✗ Loi: {e}")

print("\n" + "=" * 60)
print("KIỂM TRA HOÀN THÀNH")
print("=" * 60)
pygame.quit()
