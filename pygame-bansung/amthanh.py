# amthanh.py - Quan ly am thanh cho tro choi
import pygame
import os

class QuanLyAmThanh:
    """Quản lý tất cả âm thanh trong trò chơi"""
    
    def __init__(self):
        # Khởi tạo mixer sẽ được thực hiện sau khi pygame.init() được gọi
        self.mixer_initialized = False
        
        # Đường dẫn thư mục âm thanh (dùng đường dẫn tuyệt đối)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.am_thanh_folder = os.path.join(current_dir, 'assets', 'am_thanh')
        
        # Dictionary lưu trữ tất cả âm thanh
        self.sounds = {}
        self.music = None
        self.current_music = None
        
        # Cờ kiểm soát
        self.nhac_nen_playing = False
        self.am_thanh_that_bai_playing = False
        
        # Load tất cả âm thanh
        self._load_sounds()
    
    def _init_mixer(self):
        """Khởi tạo mixer (phải được gọi sau pygame.init())"""
        if self.mixer_initialized:
            return
        
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.mixer_initialized = True
            print("Mixer da duoc khoi tao thanh cong")
        except Exception as e:
            print(f"Loi khoi tao mixer: {e}")
    
    def _load_sounds(self):
        """Load tất cả file âm thanh từ assets/am_thanh (chỉ lưu path, load khi cần)"""
        sound_files = {
            'tien_sung': 'tieng_sung.mp3',
            'nhat_item': 'am_thanh_nhat_item.mp3',
            'that_bai': 'am_thanh_that_bai.mp3',
            'chuc_mung': 'am_thanh_chuc_mung_chien_thang.mp3',
            'boss': 'danh_boss.mp3',
            'nhac_nen': 'nhac_nen.mp3'
        }
        
        # Tìm tất cả file trong thư mục (case-insensitive)
        files_in_folder = {}
        try:
            if os.path.exists(self.am_thanh_folder):
                for f in os.listdir(self.am_thanh_folder):
                    files_in_folder[f.lower()] = os.path.join(self.am_thanh_folder, f)
                print(f"[AUDIO] Tim thay {len(files_in_folder)} file trong {self.am_thanh_folder}")
        except Exception as e:
            print(f"[AUDIO] Loi doc thu muc: {e}")
            return
        
        # Chỉ lưu path, không load ngay (lazy loading)
        for key, filename in sound_files.items():
            try:
                filename_lower = filename.lower()
                if filename_lower in files_in_folder:
                    path = files_in_folder[filename_lower]
                    self.sounds[key] = path  # Lưu path, sẽ load khi cần
                    print(f"[AUDIO] ✓ Tim thay: {key} -> {os.path.basename(path)}")
                else:
                    print(f"[AUDIO] ✗ Khong tim thay: {filename}")
            except Exception as e:
                print(f"[AUDIO] ✗ Loi load {key}: {e}")
    
    def play_nhac_nen(self):
        """Phat nhac nen lap lai"""
        self._init_mixer()
        if 'nhac_nen' not in self.sounds:
            print("[AUDIO] Khong co nhac_nen")
            return
        
        try:
            path = self.sounds['nhac_nen']
            print(f"[AUDIO] Load nhac_nen: {path}")
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
            self.current_music = 'nhac_nen'
            self.nhac_nen_playing = True
            print(f"[AUDIO] ✓ Phat nhac nen")
        except Exception as e:
            print(f"[AUDIO] ✗ Loi phat nhac nen: {e}")
    
    def play_nhac_boss(self):
        """Phat nhac boss thay the nhac nen"""
        self._init_mixer()
        if 'boss' not in self.sounds:
            print("[AUDIO] Khong co boss")
            return
        
        try:
            path = self.sounds['boss']
            print(f"[AUDIO] Load nhac boss: {path}")
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play(-1)
            self.current_music = 'boss'
            self.nhac_nen_playing = False
            print(f"[AUDIO] ✓ Phat nhac boss")
        except Exception as e:
            print(f"[AUDIO] ✗ Loi phat nhac boss: {e}")
    
    def play_am_thanh_that_bai(self):
        """Phat am thanh that bai khi nguoi choi chet"""
        self._init_mixer()
        if 'that_bai' not in self.sounds:
            print("[AUDIO] Khong co that_bai")
            return
        
        try:
            if not self.am_thanh_that_bai_playing:
                path = self.sounds['that_bai']
                print(f"[AUDIO] Load am thanh that bai: {path}")
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(0)
                self.current_music = 'that_bai'
                self.am_thanh_that_bai_playing = True
                print(f"[AUDIO] ✓ Phat am thanh that bai")
        except Exception as e:
            print(f"[AUDIO] ✗ Loi phat am thanh that bai: {e}")
    
    def play_tien_sung(self):
        """Phat am thanh ban sung"""
        self._init_mixer()
        if 'tien_sung' not in self.sounds:
            return
        
        try:
            path = self.sounds['tien_sung']
            if isinstance(path, str):
                sound = pygame.mixer.Sound(path)
            else:
                sound = path
            sound.set_volume(0.1)  # Giam am luong xuong 10%
            sound.play()
        except Exception as e:
            pass  # Khong log vi qua nhieu lan
    
    def play_nhat_item(self):
        """Phat am thanh nhat item"""
        self._init_mixer()
        if 'nhat_item' not in self.sounds:
            return
        
        try:
            path = self.sounds['nhat_item']
            if isinstance(path, str):
                sound = pygame.mixer.Sound(path)
            else:
                sound = path
            sound.set_volume(0.25)
            sound.play()
        except Exception as e:
            pass
    
    def play_chuc_mung_chien_thang(self):
        """Phat am thanh chuc mung chien thang"""
        self._init_mixer()
        if 'chuc_mung' not in self.sounds:
            print("[AUDIO] Khong co chuc_mung")
            return
        
        try:
            path = self.sounds['chuc_mung']
            print(f"[AUDIO] Load am thanh chuc mung: {path}")
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(0)
            self.current_music = 'chuc_mung'
            print(f"[AUDIO] ✓ Phat am thanh chuc mung chien thang")
        except Exception as e:
            print(f"[AUDIO] ✗ Loi phat am thanh chuc mung: {e}")
    
    def stop_music(self):
        """Dừng nhạc nền"""
        try:
            pygame.mixer.music.stop()
            self.current_music = None
            self.nhac_nen_playing = False
            self.am_thanh_that_bai_playing = False
        except Exception as e:
            print(f"Loi dung nhac: {e}")
    
    def pause_music(self):
        """Tạm dừng nhạc nền"""
        try:
            pygame.mixer.music.pause()
        except Exception as e:
            print(f"Loi tam dung nhac: {e}")
    
    def unpause_music(self):
        """Tiếp tục phát nhạc nền"""
        try:
            pygame.mixer.music.unpause()
        except Exception as e:
            print(f"Loi tiep tuc phat nhac: {e}")
    
    def is_music_playing(self):
        """Kiểm tra nhạc có đang phát không"""
        return pygame.mixer.music.get_busy()
    
    def set_volume(self, volume):
        """Đặt âm lượng (0.0 - 1.0)"""
        try:
            volume = max(0.0, min(1.0, volume))
            pygame.mixer.music.set_volume(volume)
        except Exception as e:
            print(f"Loi dat am luong: {e}")


# Tạo instance global
quan_ly_am_thanh = QuanLyAmThanh()
