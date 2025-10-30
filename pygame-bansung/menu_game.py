# menu_game.py
import pygame
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tinhdiem import QuanLyDiem
from che_do import difficulty

class MenuTroChoi:
    def __init__(self, screen, font):
        self.screen = screen
        self.font = font
        self.state = "menu"  # menu | difficulty_select | playing | gameover | input_name
        self.player_name = ""  # Ten nguoi choi dang nhap
        self.input_active = False
        self.current_score = 0  # Diem khi ket thuc
        self.victory_triggered = False  # Co hoan thanh tat ca cac dot
        self.is_victory = False  # Co phai thua cuoc hay chinh phuc
        self.leaderboard_manager = QuanLyDiem()  # Quan ly leaderboard
        btn_w, btn_h = 200, 60
        cx = (screen.get_width() - btn_w) // 2
        self.start_button = pygame.Rect(cx, 220, btn_w, btn_h)
        self.retry_button = pygame.Rect(cx, 300, btn_w, btn_h)
        
        # Difficulty select buttons
        self.normal_button = pygame.Rect(cx - 120, 220, btn_w, btn_h)
        self.hard_button = pygame.Rect(cx + 120, 220, btn_w, btn_h)
        
        # Pause (ESC) overlay
        self.paused = False
        self.pause_bg = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        self.pause_bg.fill((0, 0, 0, 160))
        self.continue_button = pygame.Rect(cx, 220, btn_w, btn_h)
        self.exit_button = pygame.Rect(cx, 300, btn_w, btn_h)
        # Try to load UI button images from assets/ui_menu
        self.ui_folder = os.path.join('assets', 'ui_menu')
        self.start_img = None
        self.retry_img = None
        self.continue_img = None
        self.exit_img = None
        self.game_over_img = None
        try:
            # load images if available; filenames expected: start.png, retry.png, continue.png, exit.png
            p = os.path.join(self.ui_folder, 'start.png')
            if os.path.exists(p):
                img = pygame.image.load(p)
                try:
                    img = img.convert_alpha()
                except Exception:
                    img = img.convert()
                self.start_img = pygame.transform.smoothscale(img, (self.start_button.width, self.start_button.height))
        except Exception:
            self.start_img = None
        try:
            p = os.path.join(self.ui_folder, 'restart.png')
            if os.path.exists(p):
                img = pygame.image.load(p)
                try:
                    img = img.convert_alpha()
                except Exception:
                    img = img.convert()
                self.retry_img = pygame.transform.smoothscale(img, (self.retry_button.width, self.retry_button.height))
        except Exception:
            self.retry_img = None
        try:
            p = os.path.join(self.ui_folder, 'continue.png')
            if os.path.exists(p):
                img = pygame.image.load(p)
                try:
                    img = img.convert_alpha()
                except Exception:
                    img = img.convert()
                self.continue_img = pygame.transform.smoothscale(img, (self.continue_button.width, self.continue_button.height))
        except Exception:
            self.continue_img = None
        try:
            p = os.path.join(self.ui_folder, 'exit.png')
            if os.path.exists(p):
                img = pygame.image.load(p)
                try:
                    img = img.convert_alpha()
                except Exception:
                    img = img.convert()
                self.exit_img = pygame.transform.smoothscale(img, (self.exit_button.width, self.exit_button.height))
        except Exception:
            self.exit_img = None
        try:
            p = os.path.join(self.ui_folder, 'game_over.png')
            if os.path.exists(p):
                img = pygame.image.load(p)
                try:
                    img = img.convert_alpha()
                except Exception:
                    img = img.convert()
                # Scale to reasonable size (width ~300px, maintain aspect ratio)
                original_w, original_h = img.get_size()
                target_w = 300
                scale_factor = target_w / original_w
                target_h = int(original_h * scale_factor)
                self.game_over_img = pygame.transform.smoothscale(img, (target_w, target_h))
        except Exception:
            self.game_over_img = None
        # compute menu exit rect (where the exit icon will be drawn) if we have an image
        if self.exit_img:
            exit_top = self.start_button.bottom + 20
            self.menu_exit_rect = pygame.Rect(cx, exit_top, btn_w, btn_h)
        else:
            self.menu_exit_rect = None

    def ve_menu(self):
        self.screen.fill((20, 20, 30))
        # Title removed per request (no "HOLDING OUT - DEMO" text)

        if self.start_img:
            # center image in button rect (image is scaled to button size when loaded)
            img_rect = self.start_img.get_rect(center=self.start_button.center)
            self.screen.blit(self.start_img, img_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (50, 200, 50), self.start_button)
            t = self.font.render("START", True, (0, 0, 0))
            t_rect = t.get_rect(center=self.start_button.center)
            self.screen.blit(t, t_rect.topleft)

        # Replace quit hint with exit image if available
        if self.exit_img:
            try:
                icon = pygame.transform.smoothscale(self.exit_img, (self.start_button.width, self.start_button.height))
            except Exception:
                icon = pygame.transform.scale(self.exit_img, (self.start_button.width, self.start_button.height))
            # place the exit icon centered horizontally and directly below the start button
            center_x = self.start_button.centerx
            center_y = self.start_button.bottom + 20 + (self.start_button.height // 2)
            icon_rect = icon.get_rect(center=(center_x, center_y))
            self.screen.blit(icon, icon_rect.topleft)
            # menu_exit_rect already computed in __init__ when image exists
        else:
            # per request: do not display "ESC to quit" text
            pass

    def ve_chon_che_do(self):
        """Hien thi menu chon che do choi"""
        self.screen.fill((20, 20, 30))
        
        # Tieu de
        title = self.font.render("Chon che do choi", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title, title_rect.topleft)
        
        # Nut Binh thuong
        pygame.draw.rect(self.screen, (50, 150, 200), self.normal_button)
        normal_text = self.font.render("Binh thuong", True, (0, 0, 0))
        normal_text_rect = normal_text.get_rect(center=self.normal_button.center)
        self.screen.blit(normal_text, normal_text_rect.topleft)
        
        # Nut Kho
        pygame.draw.rect(self.screen, (200, 50, 50), self.hard_button)
        hard_text = self.font.render("Kho", True, (0, 0, 0))
        hard_text_rect = hard_text.get_rect(center=self.hard_button.center)
        self.screen.blit(hard_text, hard_text_rect.topleft)
        
        # Mo ta
        normal_desc = self.font.render("Binh thuong: Ca 3 boss (1, 2, 3) tuong tien", True, (200, 200, 200))
        normal_desc_rect = normal_desc.get_rect(center=(self.screen.get_width() // 2, 350))
        self.screen.blit(normal_desc, normal_desc_rect.topleft)
        
        hard_desc = self.font.render("Kho: Ca 3 boss cung luc", True, (200, 200, 200))
        hard_desc_rect = hard_desc.get_rect(center=(self.screen.get_width() // 2, 400))
        self.screen.blit(hard_desc, hard_desc_rect.topleft)

    def ve_thua_cuoc(self):
        self.screen.fill((20, 5, 5))  # Màu nền tối hơn
        
        # Display game over image if available, centered horizontally (lower position)
        if self.game_over_img:
            img_rect = self.game_over_img.get_rect(center=(self.screen.get_width() // 2, 180))
            self.screen.blit(self.game_over_img, img_rect.topleft)
        else:
            # Fallback to text, centered
            title = self.font.render("GAME OVER", True, (255, 80, 80))
            title_rect = title.get_rect(center=(self.screen.get_width() // 2, 180))
            self.screen.blit(title, title_rect.topleft)

        if self.retry_img:
            img_rect = self.retry_img.get_rect(center=self.retry_button.center)
            self.screen.blit(self.retry_img, img_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (220, 200, 0), self.retry_button)
            t = self.font.render("PLAY AGAIN", True, (0, 0, 0))
            t_rect = t.get_rect(center=self.retry_button.center)
            self.screen.blit(t, t_rect.topleft)
    
    def ve_nhap_ten(self):
        """Ve man hinh nhap ten nguoi choi"""
        if self.is_victory:
            # Hien thi man hinh chinh phuc - nen vang
            self.screen.fill((30, 30, 20))
            
            # Tieu de
            title = self.font.render("CHIEN THANG!", True, (255, 255, 0))
            title_rect = title.get_rect(center=(self.screen.get_width() // 2, 80))
            self.screen.blit(title, title_rect.topleft)
        else:
            # Hien thi man hinh thua cuoc - nen toi
            self.screen.fill((20, 20, 30))
            
            # Tieu de
            title = self.font.render("NHAP TEN CUA BAN", True, (100, 200, 255))
            title_rect = title.get_rect(center=(self.screen.get_width() // 2, 100))
            self.screen.blit(title, title_rect.topleft)
        
        # Hien thi diem (vi tri khac nhau)
        score_text = self.font.render(f"Diem cua ban: {self.current_score}", True, (255, 200, 100))
        score_y = 160 if self.is_victory else 180
        score_rect = score_text.get_rect(center=(self.screen.get_width() // 2, score_y))
        self.screen.blit(score_text, score_rect.topleft)
        
        # Hop nhap lieu
        input_rect = pygame.Rect(150, 280, 660, 60)
        pygame.draw.rect(self.screen, (255, 255, 255), input_rect, 3)
        
        # Van ban nhap
        input_text = self.font.render(self.player_name if self.player_name else "Nhap ten...", True, (255, 255, 255))
        self.screen.blit(input_text, (input_rect.x + 10, input_rect.y + 15))
        
        # Nut xac nhan
        btn_rect = pygame.Rect(self.screen.get_width() // 2 - 100, 400, 200, 60)
        btn_color = (50, 150, 50) if self.player_name else (100, 100, 100)
        if self.is_victory:
            btn_color = (200, 200, 50) if self.player_name else (150, 150, 100)
        pygame.draw.rect(self.screen, btn_color, btn_rect)
        btn_text = self.font.render("XAC NHAN", True, (255, 255, 255))
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect.topleft)
        
        self.confirm_button = btn_rect
    
    def ve_leaderboard(self):
        """Ve bang xep hang cua che do hien tai"""
        self.screen.fill((20, 20, 30))
        
        # Cau nhat che do
        mode = "hard" if difficulty.is_hard_mode() else "normal"
        self.leaderboard_manager.set_current_mode(mode)
        
        # Tieu de voi ten che do
        mode_name = "Che do Kho" if mode == "hard" else "Che do Binh thuong"
        title = self.font.render(f"BANG XEP HANG - {mode_name}", True, (255, 200, 100))
        title_rect = title.get_rect(center=(self.screen.get_width() // 2, 40))
        self.screen.blit(title, title_rect.topleft)
        
        # Top scores
        top_scores = self.leaderboard_manager.get_top_scores(10)
        y = 120
        for i, entry in enumerate(top_scores, 1):
            text = f"{i}. {entry['name']}: {entry['score']} diem"
            score_text = self.font.render(text, True, (200, 200, 255) if i == 1 else (180, 180, 180))
            self.screen.blit(score_text, (50, y))
            y += 50
        
        # Nut quay lai
        back_rect = pygame.Rect(350, 520, 260, 60)
        pygame.draw.rect(self.screen, (100, 100, 150), back_rect)
        back_text = self.font.render("QUAY LAI", True, (255, 255, 255))
        back_text_rect = back_text.get_rect(center=back_rect.center)
        self.screen.blit(back_text, back_text_rect.topleft)
        self.back_button = back_rect

    def xu_ly_click(self, pos):
        if self.state == "menu":
            if self.start_button.collidepoint(pos):
                self.state = "difficulty_select"
        elif self.state == "difficulty_select":
            if self.normal_button.collidepoint(pos):
                difficulty.set_mode(difficulty.NORMAL)
                self.state = "playing"
            elif self.hard_button.collidepoint(pos):
                difficulty.set_mode(difficulty.HARD)
                self.state = "playing"
        elif self.state == "gameover":
            if self.retry_button.collidepoint(pos):
                self.state = "difficulty_select"
        elif self.state == "input_name":
            if hasattr(self, 'confirm_button') and self.confirm_button.collidepoint(pos):
                if self.player_name.strip():
                    # Luu diem vao che do hien tai
                    mode = "hard" if difficulty.is_hard_mode() else "normal"
                    self.leaderboard_manager.add_score(self.player_name, self.current_score, mode=mode)
                    self.state = "leaderboard"
                    self.player_name = ""
        elif self.state == "leaderboard":
            if hasattr(self, 'back_button') and self.back_button.collidepoint(pos):
                self.state = "menu"
    
    def handle_key_input(self, event):
        """Xu ly input khi nhap ten"""
        if self.state != "input_name":
            return
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif event.key == pygame.K_RETURN:
                if self.player_name.strip():
                    # Luu diem vao che do hien tai
                    mode = "hard" if difficulty.is_hard_mode() else "normal"
                    self.leaderboard_manager.add_score(self.player_name, self.current_score, mode=mode)
                    self.state = "leaderboard"
                    self.player_name = ""
            elif len(self.player_name) < 20:  # Gioi han do dai ten
                self.player_name += event.unicode

    def toggle_pause(self):
        """Toggle paused state while playing."""
        if self.state != "playing":
            return
        self.paused = not self.paused
        
        # Pause/unpause nhac
        try:
            from amthanh import quan_ly_am_thanh
            if self.paused:
                quan_ly_am_thanh.pause_music()
            else:
                quan_ly_am_thanh.unpause_music()
        except Exception:
            pass

    def ve_pause(self):
        """Draw the paused overlay with Continue / Exit buttons."""
        # draw translucent overlay
        try:
            self.screen.blit(self.pause_bg, (0, 0))
        except Exception:
            # fallback: draw a filled rect
            pygame.draw.rect(self.screen, (0, 0, 0), self.screen.get_rect())

        title = self.font.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(title, (self.screen.get_width() // 2 - title.get_width() // 2, 140))

        if self.continue_img:
            img_rect = self.continue_img.get_rect(center=self.continue_button.center)
            self.screen.blit(self.continue_img, img_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (50, 200, 50), self.continue_button)
            t = self.font.render("CONTINUE", True, (0, 0, 0))
            t_rect = t.get_rect(center=self.continue_button.center)
            self.screen.blit(t, t_rect.topleft)

        if self.exit_img:
            img_rect = self.exit_img.get_rect(center=self.exit_button.center)
            self.screen.blit(self.exit_img, img_rect.topleft)
        else:
            pygame.draw.rect(self.screen, (200, 50, 50), self.exit_button)
            t2 = self.font.render("EXIT", True, (0, 0, 0))
            t2_rect = t2.get_rect(center=self.exit_button.center)
            self.screen.blit(t2, t2_rect.topleft)

    def handle_pause_click(self, pos):
        """Handle clicks on pause menu buttons."""
        if self.continue_button.collidepoint(pos):
            self.paused = False
            # Phát lại nhạc
            try:
                from amthanh import quan_ly_am_thanh
                quan_ly_am_thanh.unpause_music()
            except Exception:
                pass
            return 'continue'
        if self.exit_button.collidepoint(pos):
            # return to main menu
            self.paused = False
            self.state = 'menu'
            # Dừng nhạc khi exit
            try:
                from amthanh import quan_ly_am_thanh
                quan_ly_am_thanh.stop_music()
            except Exception:
                pass
            return 'exit'
        return None

    # Alias tiếng Anh để tương thích với mã hiện có
    draw_menu = ve_menu
    draw_gameover = ve_thua_cuoc
    handle_click = xu_ly_click

# Alias tên lớp để tương thích với import cũ
GameMenu = MenuTroChoi
