import os
import re
import pygame, random
from cau_hinh import (
    ENEMY_SPEED,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
)
from ke_thu import load_animation_frames


class Boss(pygame.sprite.Sprite):
    def __init__(self, vi_tri, muc_tieu, nhom_tat_ca, nhom_dan=None):
        super().__init__()
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'boss')

        # MANUAL loader: group frames by filename prefix so we don't mix tuluc/skill into idle
        # Use consistent scaling to match other enemies (increase size to 100%)
        scale = 1.0
        buckets = {
            'dung': [],
            'di': [],
            'danh': [],
            'tuluc': [],
            'skill1_': [],
            'chet': [],
            'trungdan': [],
        }
        try:
            files = [f for f in sorted(os.listdir(assets_folder)) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        except Exception:
            files = []
        for fname in files:
            lname = fname.lower()
            path = os.path.join(assets_folder, fname)
            try:
                img = pygame.image.load(path)
                try:
                    if pygame.display.get_init():
                        img = img.convert_alpha()
                    else:
                        img = img.convert()
                except Exception:
                    pass
                try:
                    w = int(img.get_width() * scale)
                    h = int(img.get_height() * scale)
                    if w > 0 and h > 0:
                        img = pygame.transform.smoothscale(img, (w, h))
                except Exception:
                    pass
            except Exception:
                continue

            # bucket by prefix
            if lname.startswith('dung'):
                buckets['dung'].append(img)
            elif lname.startswith('di'):
                buckets['di'].append(img)
            elif lname.startswith('danh'):
                buckets['danh'].append(img)
            elif lname.startswith('tuluc'):
                buckets['tuluc'].append(img)
            elif lname.startswith('skill1_'):
                buckets['skill1_'].append(img)
            elif lname.startswith('chet'):
                buckets['chet'].append(img)
            elif lname.startswith('trungdan'):
                buckets['trungdan'].append(img)
            else:
                # fallback to idle
                buckets['dung'].append(img)

        # pick a sensible first frame from our manual buckets
        first = None
        try:
            idle_bucket = buckets.get('dung', [])
            run_bucket = buckets.get('di', [])
            if idle_bucket and len(idle_bucket) > 0:
                first = idle_bucket[0]
            elif run_bucket and len(run_bucket) > 0:
                first = run_bucket[0]
        except Exception:
            first = None
        if not first:
            first = pygame.Surface((80, 80))
            first.fill((150, 0, 0))
        self.image = first
        self.rect = self.image.get_rect(center=vi_tri)

        self.muc_tieu = muc_tieu
        self.nhom_tat_ca = nhom_tat_ca
        self.nhom_dan = nhom_dan

        # Stats
        self.hp = 10
        self.hp_toi_da = 10  # Maximum HP for health bar
        self.speed = ENEMY_SPEED * 0.9
        self.activation_range = 300
        # mark this entity as a boss for external logic
        self.is_boss = True

        # State machine
        self.state = 'spawn_idle'  # khi vừa xuất hiện
        self.state_timer = 0.0
        self.idle_duration = 2.0     # đứng yên 2 giây
        self.time_between_charge = 9.0
        self.charge_duration = 3.0
        self.charge_cooldown = self.time_between_charge
        self.dash_speed = ENEMY_SPEED * 8.0
        self.dash_target = None
        self.direction = pygame.Vector2(1, 0)

        # Use manual buckets created earlier
        self.idle_frames = buckets.get('dung', [])
        self.move_frames = buckets.get('di', [])
        self.attack_frames = buckets.get('danh', [])
        self.charge_frames = buckets.get('tuluc', [])
        self.skill_frames = buckets.get('skill1_', [])
        self.death_frames = buckets.get('chet', [])
        self.hit_frames = buckets.get('trungdan', [])

        # choose current frame lists
        self.current_move_frames = self.move_frames if self.move_frames else (self.idle_frames if self.idle_frames else None)
        self.current_attack_frames = None
        self.current_charge_frames = None
        self.current_skill_frames = None
        self.current_death_frames = None
        # hit (trungdan) state control
        self._hit_playing = False
        self.hit_timer = 0.0
        self.hit_stun_duration = 0.4
        # death hold: after last death frame, keep it visible for a short time before killing
        self.death_hold = 0.5
        self.death_hold_timer = 0.0
        self.death_started = False

        # Timers
        self.attack_range = 30
        self.attack_timer = 0.0
        self.attack_cooldown = 1.5
        self.move_timer = 0.0
        self.move_switch_interval = 1.0

        # Spawn protection (seconds) to avoid instant death on spawn
        self.spawn_protection = 0.0

        # Animation control
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.12
        self.last_touch_ticks = -999999  # Khởi tạo để va chạm có thể xảy ra ngay

    def set_state(self, s):
        if self.state == s:
            return
        self.state = s
        self.state_timer = 0.0
        self.frame_index = 0
        self.frame_timer = 0.0

    def update_animation(self, dt):
        # If currently in hit/stun state, prefer hit frames
        if self._hit_playing and self.hit_frames:
            frames = self.hit_frames
        else:
            frames = None
            if self.state == 'spawn_idle' and self.idle_frames:
                frames = self.idle_frames
            elif self.state == 'roam' and self.current_move_frames:
                frames = self.current_move_frames
            elif self.state == 'attack' and self.current_attack_frames:
                frames = self.current_attack_frames
            elif self.state == 'charging' and self.current_charge_frames:
                frames = self.current_charge_frames
            elif self.state == 'dash' and (self.current_skill_frames or self.skill_frames):
                # during dash show skill frames (visual only)
                frames = self.current_skill_frames if self.current_skill_frames else self.skill_frames
            elif self.state == 'dead' and (self.current_death_frames or self.death_frames):
                frames = self.current_death_frames if self.current_death_frames else self.death_frames
            else:
                frames = self.idle_frames if self.idle_frames else (self.move_frames if self.move_frames else None)

        if not frames:
            return
        # advance timers and frames
        self.frame_timer += dt
        # handle hit timer: while hit playing, pause other state changes visually
        if self._hit_playing:
            self.hit_timer += dt
            if self.hit_timer >= self.hit_stun_duration:
                self._hit_playing = False
                self.hit_timer = 0.0

        # If we're in the dead state, do not loop the animation — play once and remove.
        if self.state == 'dead':
            # advance death animation but do not loop; after last frame hold for death_hold then kill
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1
                else:
                    # last frame reached
                    if not self.death_started:
                        self.death_started = True
                        self.death_hold_timer = 0.0
                    else:
                        self.death_hold_timer += self.frame_duration
                    # if hold time exceeded, remove sprite
                    if self.death_hold_timer >= self.death_hold:
                        try:
                            self.kill()
                            return
                        except Exception:
                            pass
        else:
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % len(frames)
        current = frames[self.frame_index]

        # Flip theo hướng di chuyển
        try:
            if self.direction.x < 0:
                self.image = pygame.transform.flip(current, True, False)
            else:
                self.image = current
        except Exception:
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
        if self.state == 'dead':
            # play death animation and return (sprite will be killed at animation end)
            self.update_animation(dt)
            return

        self.state_timer += dt

        obstacles = vat_cans if vat_cans is not None else ()

        # ======= 1️⃣ GIAI ĐOẠN XUẤT HIỆN =======
        if self.state == 'spawn_idle':
            if self.state_timer >= self.idle_duration:
                self.set_state('roam')

        # ======= 2️⃣ DI CHUYỂN XUNG QUANH =======
        elif self.state == 'roam':
            if self.muc_tieu:
                vec = pygame.Vector2(self.muc_tieu.rect.center) - pygame.Vector2(self.rect.center)
                if vec.length() > 0:
                    self.direction = vec.normalize()
                dx = self.direction.x * self.speed * dt
                dy = self.direction.y * self.speed * dt
                self._move_axis(dx, obstacles, axis="x")
                self._move_axis(dy, obstacles, axis="y")

            if self.move_frames:
                self.move_timer += dt
                if self.move_timer >= self.move_switch_interval:
                    self.move_timer -= self.move_switch_interval
                    # loader provides a single run-frame list; keep using it
                    self.current_move_frames = self.move_frames

            # kiểm tra người chơi trong vùng kích hoạt
            if self.muc_tieu:
                dx = self.muc_tieu.rect.centerx - self.rect.centerx
                dy = self.muc_tieu.rect.centery - self.rect.centery
                dist = (dx * dx + dy * dy) ** 0.5
                if dist <= self.activation_range:
                    # Đánh nếu trong tầm
                    if dist <= self.attack_range and self.attack_timer <= 0:
                        # set attack frames from loader
                        self.current_attack_frames = self.attack_frames if self.attack_frames else None
                        self.set_state('attack')
                        self.attack_timer = self.attack_cooldown
                    # Tụ lực mỗi 9s
                    self.charge_cooldown -= dt
                    if self.charge_cooldown <= 0:
                        self.set_state('charging')
                        self.current_charge_frames = self.charge_frames if self.charge_frames else None
                        self.charge_cooldown = self.time_between_charge
                self.attack_timer = max(0.0, self.attack_timer - dt)

        # ======= 3️⃣ ĐÁNH THƯỜNG =======
        elif self.state == 'attack':
            self.update_animation(dt)
            if self.state_timer >= 0.8:
                if self.muc_tieu:
                    try:
                        self.muc_tieu.nhan_sat_thuong(1)
                    except Exception:
                        pass
                self.set_state('roam')

        # ======= 4️⃣ TỤ LỰC =======
        elif self.state == 'charging':
            if self.state_timer >= self.charge_duration:
                if self.muc_tieu:
                    self.dash_target = pygame.Vector2(self.muc_tieu.rect.center)
                else:
                    self.dash_target = pygame.Vector2(self.rect.center)
                dir_vec = self.dash_target - pygame.Vector2(self.rect.center)
                self.dash_dir = dir_vec.normalize() if dir_vec.length() > 0 else pygame.Vector2(1, 0)
                # set skill frames to play during dash
                self.current_skill_frames = self.skill_frames if self.skill_frames else None
                self.set_state('dash')

        # ======= 5️⃣ LAO TỚI NGƯỜI CHƠI =======
        elif self.state == 'dash':
            move = self.dash_dir * self.dash_speed * dt
            self._move_axis(move.x, obstacles, axis="x")
            self._move_axis(move.y, obstacles, axis="y")
            try:
                if self.muc_tieu and self.rect.colliderect(self.muc_tieu.rect):
                    self.muc_tieu.nhan_sat_thuong(3)
            except Exception:
                pass
            if self.state_timer >= 1.0:
                self.set_state('roam')

        # Giữ boss trong vùng map thực tế
        vung = pygame.Rect(
            MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_TOP,
            MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
        )
        self.rect.clamp_ip(vung)

        # Cập nhật animation
        self.update_animation(dt)

        # Advance spawn protection timer
        if self.spawn_protection > 0:
            self.spawn_protection = max(0.0, self.spawn_protection - dt)

    def take_damage(self, amount=1):
        # Ignore damage while spawn protection active
        if getattr(self, 'spawn_protection', 0.0) > 0:
            return
        self.hp -= amount
        if self.hp <= 0:
            # pick death frames and switch to dead state
            self.current_death_frames = self.death_frames if self.death_frames else None
            self.set_state('dead')
        else:
            # play hit (trungdan) animation and stun briefly
            if self.hit_frames:
                self._hit_playing = True
                self.hit_timer = 0.0
                # reset frame index to show hit animation from start
                self.frame_index = 0
                self.frame_timer = 0.0

    def ve_thanh_mau(self, man_hinh, offset):
        """Vẽ thanh máu phía trên đầu boss"""
        if self.hp <= 0:
            return  # Don't draw health bar if dead
        
        # Health bar dimensions (larger for boss)
        bar_width = 60
        bar_height = 6
        bar_x = self.rect.centerx - bar_width // 2 - offset[0]
        bar_y = self.rect.top - 15 - offset[1]
        
        # Background (red)
        pygame.draw.rect(man_hinh, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Foreground (green) - current HP
        current_width = int((self.hp / self.hp_toi_da) * bar_width)
        if current_width > 0:
            pygame.draw.rect(man_hinh, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))

    # Alias for Vietnamese compatibility
    nhan_sat_thuong = take_damage

    cap_nhat = update

