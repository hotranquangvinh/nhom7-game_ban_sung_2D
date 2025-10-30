"""
Che do choi: Binh thuong, Kho
"""

class DifficultyMode:
    """Quan ly che do kho"""
    NORMAL = "normal"
    HARD = "hard"
    
    def __init__(self):
        self.current_mode = self.NORMAL
    
    def set_mode(self, mode):
        """Dat che do choi"""
        if mode in [self.NORMAL, self.HARD]:
            self.current_mode = mode
    
    def is_normal_mode(self):
        """Kiem tra che do binh thuong"""
        return self.current_mode == self.NORMAL
    
    def is_hard_mode(self):
        """Kiem tra che do kho"""
        return self.current_mode == self.HARD
    
    def get_mode_name(self):
        """Lay ten che do"""
        if self.current_mode == self.NORMAL:
            return "Binh thuong"
        elif self.current_mode == self.HARD:
            return "Kho"
        return "Unknown"


# Global instance
difficulty = DifficultyMode()
