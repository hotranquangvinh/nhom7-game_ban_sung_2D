import json
import os
from datetime import datetime

class QuanLyDiem:
    """Quan ly diem so va xep hang cua nguoi choi - tach rieng theo che do"""
    
    def __init__(self, file_path_normal="leaderboard_normal.json", file_path_hard="leaderboard_hard.json"):
        self.file_path_normal = file_path_normal
        self.file_path_hard = file_path_hard
        self.leaderboard_normal = []
        self.leaderboard_hard = []
        self.current_mode = "normal"  # che do hien tai
        self.load_leaderboards()
    
    def load_leaderboards(self):
        """Tai danh sach xep hang tu files"""
        # Load normal mode
        if os.path.exists(self.file_path_normal):
            try:
                with open(self.file_path_normal, 'r', encoding='utf-8') as f:
                    self.leaderboard_normal = json.load(f)
            except Exception as e:
                print(f"Loi khi tai leaderboard normal: {e}")
                self.leaderboard_normal = []
        else:
            self.leaderboard_normal = []
        
        # Load hard mode
        if os.path.exists(self.file_path_hard):
            try:
                with open(self.file_path_hard, 'r', encoding='utf-8') as f:
                    self.leaderboard_hard = json.load(f)
            except Exception as e:
                print(f"Loi khi tai leaderboard hard: {e}")
                self.leaderboard_hard = []
        else:
            self.leaderboard_hard = []
    
    def set_current_mode(self, mode):
        """Dat che do hien tai (normal hoac hard)"""
        if mode in ("normal", "hard"):
            self.current_mode = mode
    
    def get_current_leaderboard(self):
        """Lay leaderboard cua che do hien tai"""
        if self.current_mode == "hard":
            return self.leaderboard_hard
        else:
            return self.leaderboard_normal
    
    def save_leaderboards(self):
        """Luu danh sach xep hang vao files"""
        try:
            with open(self.file_path_normal, 'w', encoding='utf-8') as f:
                json.dump(self.leaderboard_normal, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Loi khi luu leaderboard normal: {e}")
        
        try:
            with open(self.file_path_hard, 'w', encoding='utf-8') as f:
                json.dump(self.leaderboard_hard, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Loi khi luu leaderboard hard: {e}")
    
    def add_score(self, player_name, score, mode=None):
        """Them diem so cua nguoi choi vao danh sach theo che do"""
        if mode is None:
            mode = self.current_mode
        
        entry = {
            'name': player_name,
            'score': score,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if mode == "hard":
            self.leaderboard_hard.append(entry)
            self.leaderboard_hard.sort(key=lambda x: x['score'], reverse=True)
            self.leaderboard_hard = self.leaderboard_hard[:100]
        else:
            self.leaderboard_normal.append(entry)
            self.leaderboard_normal.sort(key=lambda x: x['score'], reverse=True)
            self.leaderboard_normal = self.leaderboard_normal[:100]
        
        self.save_leaderboards()
    
    def get_top_scores(self, limit=10, mode=None):
        """Lay top diem so theo che do"""
        if mode is None:
            mode = self.current_mode
        
        if mode == "hard":
            return self.leaderboard_hard[:limit]
        else:
            return self.leaderboard_normal[:limit]
    
    def get_high_score(self, mode=None):
        """Lay diem cao nhat theo che do"""
        if mode is None:
            mode = self.current_mode
        
        leaderboard = self.leaderboard_hard if mode == "hard" else self.leaderboard_normal
        if leaderboard:
            return leaderboard[0]['score']
        return 0
    
    def get_high_score_player(self, mode=None):
        """Lay ten nguoi choi co diem cao nhat theo che do"""
        if mode is None:
            mode = self.current_mode
        
        leaderboard = self.leaderboard_hard if mode == "hard" else self.leaderboard_normal
        if leaderboard:
            return leaderboard[0]['name']
        return "Khong co"


class TinhDiem:
    """Tinh diem dua tren cac hanh dong trong game"""
    
    # Dinh nghia diem cho tung loai ke thu
    DIEM_KE_THU_1 = 1          # ke_thu.py
    DIEM_KE_THU_2_3 = 2        # ke_thu_2.py, ke_thu_3.py
    DIEM_BOSS_1 = 10           # boss.py
    DIEM_BOSS_2 = 15           # boss2.py
    DIEM_BOSS_3 = 30           # boss3.py (boss cuoi)
    TRAT_DIEM_BI_BAN = -1      # Bi ban tru 1 diem
    
    def __init__(self):
        self.diem = 0
    
    def reset(self):
        """Reset diem ve 0"""
        self.diem = 0
    
    def cong_diem_tieu_diet_ke_thu(self, enemy_type):
        """Cong diem khi tieu diet ke thu
        
        enemy_type: 
            - 'enemy_1': ke thu loai 1 (1 diem)
            - 'enemy_2': ke thu loai 2 (2 diem)
            - 'enemy_3': ke thu loai 3 (2 diem)
            - 'boss_1': boss 1 (10 diem)
            - 'boss_2': boss 2 (15 diem)
            - 'boss_3': boss 3 (30 diem - boss cuoi)
        """
        diem_cong = 0
        
        if enemy_type == 'enemy_1':
            diem_cong = self.DIEM_KE_THU_1
        elif enemy_type == 'enemy_2':
            diem_cong = self.DIEM_KE_THU_2_3
        elif enemy_type == 'enemy_3':
            diem_cong = self.DIEM_KE_THU_2_3
        elif enemy_type == 'boss_1':
            diem_cong = self.DIEM_BOSS_1
        elif enemy_type == 'boss_2':
            diem_cong = self.DIEM_BOSS_2
        elif enemy_type == 'boss_3':
            diem_cong = self.DIEM_BOSS_3
        
        self.diem += diem_cong
        return diem_cong
    
    def trat_diem_bi_dan(self):
        """Tru diem khi bi ban"""
        self.diem = max(0, self.diem + self.TRAT_DIEM_BI_BAN)
        return self.TRAT_DIEM_BI_BAN
    
    def get_diem(self):
        """Lay diem hien tai"""
        return max(0, self.diem)
