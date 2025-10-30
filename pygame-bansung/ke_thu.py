# ke_thu.py - Đối tượng kẻ thù (animation + movement + shooting)
import os
import pygame, random
from dan import Bullet
from cau_hinh import (
    ENEMY_SPEED,
    ENEMY_SHOOT_INTERVAL_MIN,
    ENEMY_SHOOT_INTERVAL_MAX,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
)


def _strip_accents(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def _numeric_key(s):
    # split into text and numbers so that chay1,chay2,... sorts naturally
    import re
    parts = re.split(r'(\d+)', s)
    key = []
    for p in parts:
        if p.isdigit():
            key.append(int(p))
        else:
            key.append(p.lower())
    return key


def load_animation_frames(folder):
    """Load images from folder and bucket them into actions: idle/run/shoot/dead.

    Filenames are normalized (strip accents) and sorted with numeric-aware ordering.
    Keywords heuristics (after stripping accents):
      'dung' -> idle, 'chay' or 'chayphai' -> run, 'ban' -> shoot, 'chet' -> dead.
    """
    frames = {"idle": [], "run": [], "shoot": [], "dead": []}
    if not os.path.isdir(folder):
        return frames

    files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    # normalize names for sorting and grouping
    normalized = [(f, _strip_accents(f).lower()) for f in files]
    normalized.sort(key=lambda x: _numeric_key(x[1]))

    for f, name_norm in normalized:
        path = os.path.join(folder, f)
        try:
            img = pygame.image.load(path)
            # convert_alpha requires a display surface initialized on some systems
            try:
                if pygame.display.get_init():
                    img = img.convert_alpha()
                else:
                    # convert without alpha to be safe
                    img = img.convert()
            except Exception:
                # fallback: keep original surface
                pass
        except Exception:
            continue
        # scale image by ENEMY_SPRITE_SCALE if not 1.0
        try:
            # Tăng kích cỡ kẻ thù lên (100% kích thước gốc)
            scale = 1.0
            w = int(img.get_width() * scale)
            h = int(img.get_height() * scale)
            if w > 0 and h > 0:
                img = pygame.transform.smoothscale(img, (w, h))
        except Exception:
            pass

        # choose bucket using normalized name
        if 'dung' in name_norm:
            frames['idle'].append(img)
        elif 'chet' in name_norm:
            frames['dead'].append(img)
        elif 'ban' in name_norm or 'danh' in name_norm:
            frames['shoot'].append(img)
        elif 'chay' in name_norm or 'di' in name_norm:
            frames['run'].append(img)
        else:
            frames['idle'].append(img)

    return frames


class Enemy(pygame.sprite.Sprite):
    def __init__(self, vi_tri, muc_tieu_nguoi_choi, nhom_tat_ca_sprite, nhom_dan, item_manager=None):
        """
        Enemy with simple random movement, occasional shooting, and animation states.
        """
        super().__init__()

        # references
        self.muc_tieu = muc_tieu_nguoi_choi
        self.nhom_tat_ca = nhom_tat_ca_sprite
        self.nhom_dan = nhom_dan

        # movement
        self.toc_do = ENEMY_SPEED
        # Default random direction
        self.huong = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        if self.huong.length() == 0:
            self.huong = pygame.Vector2(1, 0)
        else:
            self.huong = self.huong.normalize()

        # If spawned outside the visible screen, direct enemy into the screen
        try:
            man_hinh = pygame.display.get_surface()
            if man_hinh:
                screen_rect = man_hinh.get_rect()
                # If initial position is outside the screen, point towards player if available, else center
                if not screen_rect.collidepoint(vi_tri):
                    if self.muc_tieu:
                        dx = self.muc_tieu.rect.centerx - vi_tri[0]
                        dy = self.muc_tieu.rect.centery - vi_tri[1]
                    else:
                        cx, cy = screen_rect.center
                        dx = cx - vi_tri[0]
                        dy = cy - vi_tri[1]
                    vec = pygame.Vector2(dx, dy)
                    if vec.length() != 0:
                        self.huong = vec.normalize()
        except Exception:
            # ignore if display not initialized or other issues
            pass

        self.thoi_gian_doi_huong = random.uniform(1.0, 2.5)
        self.dem_doi_huong = 0.0

        # shooting: fixed cooldown for bat enemy (2.0 seconds between shots)
        self.khoang_thoi_gian_ban = 2.0
        self.dem_ban = 0.0

        # animation
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'ke_thu')
        self.anim = load_animation_frames(assets_folder)
        # if no frames loaded, create a fallback surface
        if not any(self.anim.values()):
            surf = pygame.Surface((30, 30))
            surf.fill((200, 60, 60))
            self.anim['idle'] = [surf]

        self.state = 'idle'  # idle, run, shoot, dead
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.12

        # initial image and rect
        first = self.anim.get('idle')[0] if self.anim.get('idle') else list(next(iter(self.anim.values())))[0]
        self.image = first
        self.rect = self.image.get_rect(center=vi_tri)

        # hp for possible hits
        self.hp = 2  # Cần 2 đạn để tiêu diệt
        self.hp_toi_da = 2  # Maximum HP for health bar

        # shoot-state helper
        self._shoot_playing = False
        self.last_touch_ticks = -999999  # Khởi tạo để va chạm có thể xảy ra ngay

    def set_state(self, s):
        if s == self.state:
            return
        # once dead, don't change to any other state
        if getattr(self, 'state', None) == 'dead' and s != 'dead':
            return
        # debug removed
        self.state = s
        self.frame_index = 0
        self.frame_timer = 0.0
        self._shoot_playing = (s == 'shoot')

    def update_animation(self, dt):
        frames = self.anim.get(self.state) or self.anim.get('idle')
        if not frames:
            return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if self.state == 'shoot':
                    # after shooting, return to idle/run
                    self._shoot_playing = False
                    self.set_state('idle')
                    frames = self.anim.get(self.state) or frames
                elif self.state == 'dead':
                    # end of dead animation -> remove
                    self.kill()
                    return
                else:
                    # loop
                    self.frame_index = 0
        # choose frame and flip if needed
        current = frames[self.frame_index % len(frames)]
        if self.huong.x < 0:
            self.image = pygame.transform.flip(current, True, False)
        else:
            self.image = current

    def _move_axis(self, delta, obstacles, axis="x"):
        """Di chuyển theo một trục với kiểm tra va chạm vật cản."""
        if delta == 0:
            return False

        if axis == "x":
            self.rect.x += delta
        else:
            self.rect.y += delta

        collided = False
        for vat_can in obstacles:
            if not self.rect.colliderect(vat_can.rect):
                continue
            collided = True
            if axis == "x":
                if delta > 0:
                    self.rect.right = vat_can.rect.left
                else:
                    self.rect.left = vat_can.rect.right
            else:
                if delta > 0:
                    self.rect.bottom = vat_can.rect.top
                else:
                    self.rect.top = vat_can.rect.bottom
        return collided

    def update(self, dt, vat_cans=None):
        # If dead: only advance animation and do nothing else
        if self.state == 'dead':
            self.update_animation(dt)
            return

        # Respect timestop freeze: if freeze_end is set and in the future, do nothing
        try:
            now_ms = pygame.time.get_ticks()
            if getattr(self, 'freeze_end', 0) > now_ms:
                # do not move, shoot, or animate while frozen
                return
        except Exception:
            pass

        obstacles = vat_cans if vat_cans is not None else ()

        # Di chuyển với kiểm tra va chạm vật cản
        dx = self.huong.x * self.toc_do * dt
        dy = self.huong.y * self.toc_do * dt

        va_cham_x = self._move_axis(dx, obstacles, axis="x")
        va_cham_y = self._move_axis(dy, obstacles, axis="y")

        # Đổi hướng khi va chạm vật cản hoặc biên
        if va_cham_x:
            self.huong.x *= -1
        if va_cham_y:
            self.huong.y *= -1

        # Giữ trong vùng map thực tế và đổi hướng khi chạm biên
        vung = pygame.Rect(
            MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_TOP,
            MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
        )
        if self.rect.left < vung.left:
            self.rect.left = vung.left
            self.huong.x *= -1
        elif self.rect.right > vung.right:
            self.rect.right = vung.right
            self.huong.x *= -1
        if self.rect.top < vung.top:
            self.rect.top = vung.top
            self.huong.y *= -1
        elif self.rect.bottom > vung.bottom:
            self.rect.bottom = vung.bottom
            self.huong.y *= -1

        # Đảm bảo không vượt quá biên
        self.rect.clamp_ip(vung)

        # Target player: move toward player instead of random wandering
        self.dem_doi_huong += dt
        if self.dem_doi_huong >= self.thoi_gian_doi_huong:
            self.dem_doi_huong = 0.0
            self.thoi_gian_doi_huong = random.uniform(0.3, 0.8)  # Update direction more frequently to track player
            # Calculate direction toward player
            if self.muc_tieu and hasattr(self.muc_tieu, 'rect'):
                dx = self.muc_tieu.rect.centerx - self.rect.centerx
                dy = self.muc_tieu.rect.centery - self.rect.centery
                vec = pygame.Vector2(dx, dy)
                if vec.length() != 0:
                    self.huong = vec.normalize()
                else:
                    self.huong = pygame.Vector2(1, 0)
            else:
                # fallback to random if no target
                self.huong = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if self.huong.length() == 0:
                    self.huong = pygame.Vector2(1, 0)
                else:
                    self.huong = self.huong.normalize()

        # Chọn trạng thái chạy/idle tùy vận tốc
        if abs(self.huong.x) > 0.1 or abs(self.huong.y) > 0.1:
            if not self._shoot_playing:
                self.set_state('run')
        else:
            if not self._shoot_playing:
                self.set_state('idle')

        # Bắn
        self.dem_ban += dt
        if self.dem_ban >= self.khoang_thoi_gian_ban:
            self.dem_ban = 0.0
            # enforce fixed cooldown of 2.0s between shots for this enemy
            self.khoang_thoi_gian_ban = 2.0
            self.ban_ve_phia_nguoi_choi()

        # Cập nhật animation (frame)
        self.update_animation(dt)

    def ban_ve_phia_nguoi_choi(self):
        if not self.muc_tieu:
            return
        dx = self.muc_tieu.rect.centerx - self.rect.centerx
        dy = self.muc_tieu.rect.centery - self.rect.centery
        vec = pygame.Vector2(dx, dy)
        if vec.length() == 0:
            vec = pygame.Vector2(1, 0)
        vien_dan = Bullet(self.rect.center, vec, owner='enemy')
        self.nhom_tat_ca.add(vien_dan)
        self.nhom_dan.add(vien_dan)
        # play shoot animation once
        self.set_state('shoot')

    def take_damage(self, amount=1):
        self.hp -= amount
        # debug removed
        if self.hp <= 0:
            self.set_state('dead')

    def ve_thanh_mau(self, man_hinh, offset):
        """Vẽ thanh máu phía trên đầu kẻ thù"""
        if self.hp <= 0:
            return  # Don't draw health bar if dead
        
        # Health bar dimensions
        bar_width = 40
        bar_height = 4
        bar_x = self.rect.centerx - bar_width // 2 - offset[0]
        bar_y = self.rect.top - 10 - offset[1]
        
        # Background (red)
        pygame.draw.rect(man_hinh, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Foreground (green) - current HP
        current_width = int((self.hp / self.hp_toi_da) * bar_width)
        if current_width > 0:
            pygame.draw.rect(man_hinh, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))

    # Alias for Vietnamese compatibility
    nhan_sat_thuong = take_damage

