# ke_thu_3.py - Kẻ thù 3: nhảy tới người chơi, gây sát thương, bị khựng khi trúng đạn
import os
import pygame, random
from cau_hinh import ENEMY_SPEED, MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, MAP_PLAYABLE_RIGHT, MAP_PLAYABLE_BOTTOM
from ke_thu import load_animation_frames

class JumperEnemy(pygame.sprite.Sprite):
    """
    Kẻ thù 3: đi bộ 5s, nhảy tới người chơi, lùi ra, lặp lại. Bị khựng khi trúng đạn.
    """
    def __init__(self, vi_tri, muc_tieu_nguoi_choi, nhom_tat_ca_sprite, item_manager=None):
        super().__init__()
        # Load animation từ assets/ke_thu_3
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'ke_thu_3')
        self.anim = load_animation_frames(assets_folder)
        # Scale frames to 90% (larger than before)
        try:
            scale = 0.9
            for k, frames in list(self.anim.items()):
                scaled = []
                for f in frames:
                    try:
                        w = int(f.get_width() * scale)
                        h = int(f.get_height() * scale)
                        if w > 0 and h > 0:
                            sf = pygame.transform.smoothscale(f, (w, h))
                        else:
                            sf = f
                    except Exception:
                        sf = f
                    scaled.append(sf)
                self.anim[k] = scaled
        except Exception:
            pass
        # Fallback nếu không có frames
        if not any(self.anim.values()):
            surf = pygame.Surface((40, 40))
            surf.fill((80, 200, 220))
            self.anim['idle'] = [surf]
        # Animation state
        self.state = 'idle'
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.12
        # Initial image and rect
        first = self.anim.get('idle')[0] if self.anim.get('idle') else list(next(iter(self.anim.values())))[0]
        self.image = first
        self.rect = self.image.get_rect(center=vi_tri)
        # References
        self.muc_tieu = muc_tieu_nguoi_choi
        self.nhom_tat_ca = nhom_tat_ca_sprite
        self.item_manager = item_manager
        # Combat
        self.hp = 3
        self.hp_toi_da = 3  # Maximum HP for health bar
        self.toc_do = ENEMY_SPEED * 1.0
        # AI state
        self.mode = 'walk'  # walk, jump, retreat, stunned
        self.mode_timer = 0.0
        self.walk_duration = 5.0
        self.jump_duration = 1.2  # Thời gian nhảy (tăng để nhảy xa hơn)
        self.retreat_duration = 1.0
        self.stun_timer = 0.0
        self.stun_duration = 1.0
        self.jump_speed = ENEMY_SPEED * 3.0
        self.retreat_speed = ENEMY_SPEED * 1.5
        self.huong = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1)).normalize() if random.random() > 0.1 else pygame.Vector2(1, 0)
        self.jump_vector = pygame.Vector2(0, 0)
        self.retreat_vector = pygame.Vector2(0, 0)
        self.last_player_pos = None
        self.is_jumping = False
        self.is_retreating = False
        self.is_stunned = False
        self.attack_range = 50
        self.attack_damage = 1
        self.is_melee = False
        self.last_touch_ticks = -999999  # Khởi tạo để va chạm có thể xảy ra ngay
    def _move_axis(self, delta, obstacles, axis="x"):
        """Move along one axis and check collision with obstacles"""
        if axis == "x":
            self.rect.x += delta
        else:
            self.rect.y += delta
        # Check collision with obstacles
        for obs in obstacles:
            if self.rect.colliderect(obs.rect):
                # Collision - push back
                if axis == "x":
                    if delta > 0:  # Moving right
                        self.rect.right = obs.rect.left
                    else:  # Moving left
                        self.rect.left = obs.rect.right
                else:  # axis == "y"
                    if delta > 0:  # Moving down
                        self.rect.bottom = obs.rect.top
                    else:  # Moving up
                        self.rect.top = obs.rect.bottom
                break
    def set_state(self, s):
        if s == self.state:
            return
        if getattr(self, 'state', None) == 'dead' and s != 'dead':
            return
        self.state = s
        self.frame_index = 0
        self.frame_timer = 0.0
    def update_animation(self, dt):
        frames = self.anim.get(self.state) or self.anim.get('idle')
        if not frames:
            return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if self.state == 'dead':
                    self.kill()
                    return
                else:
                    self.frame_index = 0
        current = frames[self.frame_index % len(frames)]
        if self.huong.x < 0:
            self.image = pygame.transform.flip(current, True, False)
        else:
            self.image = current
    def update(self, dt, vat_cans=None):
        obstacles = vat_cans if vat_cans is not None else ()

        # If dead, only animate
        if self.state == 'dead':
            self.update_animation(dt)
            return

        # Respect timestop freeze: if freeze_end is set and in the future, do nothing
        try:
            now_ms = pygame.time.get_ticks()
            if getattr(self, 'freeze_end', 0) > now_ms:
                return
        except Exception:
            pass

        # Stunned: đứng yên, đếm timer
        if self.is_stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.is_stunned = False
                self.mode = 'walk'
                self.mode_timer = 0.0
                self.set_state('run')
            self.update_animation(dt)
            return
        # Walk mode: đi bộ ngẫu nhiên 5s
        if self.mode == 'walk':
            self.mode_timer += dt
            self.set_state('run')
            dx = self.huong.x * self.toc_do * dt
            dy = self.huong.y * self.toc_do * dt
            self._move_axis(dx, obstacles, axis="x")
            self._move_axis(dy, obstacles, axis="y")
            # Đổi hướng ngẫu nhiên mỗi 1.5s
            if int(self.mode_timer * 10) % 15 == 0:
                self.huong = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if self.huong.length() == 0:
                    self.huong = pygame.Vector2(1, 0)
                else:
                    self.huong = self.huong.normalize()
            if self.mode_timer >= self.walk_duration:
                self.mode = 'jump'
                self.mode_timer = 0.0
                self.set_state('shoot')
                # Chuẩn bị vector nhảy tới player
                # Lưu lại vị trí người chơi làm điểm đến cố định cho cú nhảy
                if self.muc_tieu:
                    self.jump_target = pygame.Vector2(self.muc_tieu.rect.center)
                else:
                    self.jump_target = pygame.Vector2(self.rect.center) + pygame.Vector2(1, 0) * 120
                self.is_jumping = True
        # Jump mode: lao nhanh tới vị trí player
        elif self.mode == 'jump':
            self.set_state('shoot')
            self.mode_timer += dt
            if self.is_jumping:
                # Chỉ nhảy về đúng vị trí người chơi tại thời điểm bắt đầu nhảy
                target_pos = self.jump_target
                current_pos = pygame.Vector2(self.rect.center)
                direction = target_pos - current_pos
                distance = direction.length()
                if distance != 0:
                    direction = direction.normalize()
                move_step = direction * self.jump_speed * dt
                if move_step.length() >= distance or distance == 0:
                    dx = target_pos.x - self.rect.centerx
                    dy = target_pos.y - self.rect.centery
                    self._move_axis(dx, obstacles, axis="x")
                    self._move_axis(dy, obstacles, axis="y")
                else:
                    dx = move_step.x
                    dy = move_step.y
                    self._move_axis(dx, obstacles, axis="x")
                    self._move_axis(dy, obstacles, axis="y")
            if self.mode_timer >= self.jump_duration:
                self.mode = 'retreat'
                self.mode_timer = 0.0
                self.set_state('run')
                # Retreat vector: ngược hướng nhảy
                self.retreat_vector = -self.jump_vector
                self.is_jumping = False
                self.is_retreating = True
        # Retreat mode: lùi ra khỏi vị trí player
        elif self.mode == 'retreat':
            self.set_state('run')
            self.mode_timer += dt
            if self.is_retreating:
                dx = self.retreat_vector.x * self.retreat_speed * dt
                dy = self.retreat_vector.y * self.retreat_speed * dt
                self._move_axis(dx, obstacles, axis="x")
                self._move_axis(dy, obstacles, axis="y")
            if self.mode_timer >= self.retreat_duration:
                self.mode = 'walk'
                self.mode_timer = 0.0
                self.is_retreating = False
                self.set_state('run')
        # Keep in playable map bounds
        vung = pygame.Rect(
            MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_TOP,
            MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
        )
        self.rect.clamp_ip(vung)
        self.update_animation(dt)
    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.set_state('dead')
        else:
            # Bị khựng lại 1s
            self.is_stunned = True
            self.stun_timer = self.stun_duration
            self.mode = 'stunned'
            self.set_state('idle')
    
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
    
    # Alias for compatibility
    nhan_sat_thuong = take_damage
    cap_nhat = update

