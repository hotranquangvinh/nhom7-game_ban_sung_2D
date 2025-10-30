import os
import random
import math
import pygame
from cau_hinh import (
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
)
from dan import Bullet


class LightningEffect(pygame.sprite.Sprite):
    """Hieu ung set su dung assets/samset/set1-set10.png.
    Hien thi hoat hinh va gay sat thuong -2 mau."""
    def __init__(self, x, y, nm_all_sprites, owner_boss=None, damage=2, radius=60):
        super().__init__()
        self.x = x
        self.y = y
        self.all_sprites = nm_all_sprites
        self.owner = owner_boss
        self.damage = damage
        self.radius = radius
        self.frames = []
        self.current_frame = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.08  # 0.08s moi frame
        self.damage_applied = False
        
        # Load 10 frames tu assets/samset/set1.png - set10.png
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'samset')
        
        try:
            for i in range(1, 11):  # set1 to set10
                fname = f'set{i}.png'
                path = os.path.join(assets_folder, fname)
                if os.path.exists(path):
                    try:
                        img = pygame.image.load(path)
                        try:
                            if pygame.display.get_init():
                                img = img.convert_alpha()
                            else:
                                img = img.convert()
                        except Exception:
                            pass
                        # Scale up 1.5x - nho hon
                        w, h = img.get_size()
                        img = pygame.transform.scale(img, (int(w * 1.5), int(h * 1.5)))
                        self.frames.append(img)
                    except Exception:
                        pass
        except Exception:
            pass
        
        if self.frames:
            self.image = self.frames[0]
        else:
            # Fallback: tao hinh tam thoi
            self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.total_duration = len(self.frames) * self.frame_duration
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed += dt
        self.frame_timer += dt
        
        # Gay sat thuong lan dau khi xuat hien
        if not self.damage_applied:
            self.damage_applied = True
            self._apply_damage()
        
        # Chuyen frame
        if self.frame_timer >= self.frame_duration and self.frames:
            self.frame_timer -= self.frame_duration
            self.current_frame += 1
            
            if self.current_frame < len(self.frames):
                self.image = self.frames[self.current_frame]
            else:
                # Het animation, xoa
                self.kill()
    
    def _apply_damage(self):
        """Gay sat thuong cho nguoi choi neu trong vung hoat dong."""
        owner = getattr(self, 'owner', None)
        if owner is not None and getattr(owner, 'muc_tieu', None) is not None:
            player = owner.muc_tieu
            try:
                px, py = player.rect.center
                # Kiem tra khoang cach
                dist = math.hypot(px - self.x, py - self.y)
                if dist <= self.radius:
                    # Gay sat thuong
                    try:
                        player.nhan_sat_thuong(self.damage)
                    except Exception:
                        try:
                            player.hp = max(0, getattr(player, 'hp', 0) - self.damage)
                        except Exception:
                            pass
            except Exception:
                pass


class FallingBomb(pygame.sprite.Sprite):
    """Large falling bomb: spawns above map, falls, explodes on ground impact.
    Explosion deals area damage to player (and could be extended to other sprites).
    """
    def __init__(self, x, start_y, target_y, nm_all_sprites, nm_bullets, owner_boss=None, damage=2, radius=80):
        super().__init__()
        self.image = pygame.Surface((24, 40), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (120, 20, 20), self.image.get_rect())
        self.rect = self.image.get_rect(center=(x, int(start_y)))
        self.vy = 0.0
        self.gravity = 900.0  # px/s^2, quick fall
        self.target_y = target_y
        self.damage = damage
        self.radius = radius
        self.all_sprites = nm_all_sprites
        self.bullets_group = nm_bullets
        self.owner = owner_boss
        self.exploded = False

    def update(self, dt):
        if self.exploded:
            return
        self.vy += self.gravity * dt
        self.rect.y += int(self.vy * dt)
        # if reached or passed ground
        ground_y = self.target_y
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self._explode()

    def _explode(self):
        if self.exploded:
            return
        self.exploded = True
        # Visual: expand a circle surface and then kill after short time
        explosion = Explosion(self.rect.center, self.radius)
        try:
            if self.all_sprites is not None:
                self.all_sprites.add(explosion)
            # attach a reference to owner so explosion handler can access boss.muc_tieu
            if self.owner is not None:
                setattr(explosion, 'owner', self.owner)
        except Exception:
            pass
        # remove the bomb
        try:
            self.kill()
        except Exception:
            pass


class Explosion(pygame.sprite.Sprite):
    """Visual explosion and immediate damage application on create."""
    def __init__(self, center, radius, duration=0.45):
        super().__init__()
        size = int(radius * 2)
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 160, 0, 180), (radius, radius), radius)
        self.image = surf
        self.rect = self.image.get_rect(center=center)
        self.timer = duration
        self.duration = duration
        # damage and owner should be set by caller via attributes if needed

    def update(self, dt):
        # On first frame, try to apply damage to player if owner provided
        if getattr(self, '_applied', False) is False:
            self._applied = True
            owner = getattr(self, 'owner', None)
            if owner is not None and getattr(owner, 'muc_tieu', None) is not None:
                player = owner.muc_tieu
                try:
                    px, py = player.rect.center
                    # distance check
                    cx, cy = self.rect.center
                    dist = math.hypot(px - cx, py - cy)
                    rad = self.rect.width // 2
                    if dist <= rad:
                        # apply damage - try common method
                        try:
                            player.nhan_sat_thuong(2)
                        except Exception:
                            try:
                                player.hp = max(0, getattr(player, 'hp', 0) - 2)
                            except Exception:
                                pass
                except Exception:
                    pass

        self.timer -= dt
        if self.timer <= 0:
            try:
                self.kill()
            except Exception:
                pass


class Boss3(pygame.sprite.Sprite):
    """Boss3: stationary center boss with three skills.

    - Stands at center of playable area.
    - Attack every 3s: burst of 3 shots fired rapidly (short interval between shots).
    - Skill2: radial volley of 10 bullets launched simultaneously outward from positions around boss.
    - Skill3: spawn 3 falling bombs from above; when they hit ground they explode (area damage).
    """
    def __init__(self, vi_tri, muc_tieu, nhom_tat_ca, nhom_dan=None):
        super().__init__()
        # Load animations from assets/boss3
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'boss3')
        buckets = {
            'dung': [],
            'danh': [],
            'skill1': [],
            'skill2': [],
            'skill3': [],
            'chet': [],
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
            except Exception:
                continue

            if lname.startswith('dung'):
                buckets['dung'].append(img)
            elif lname.startswith('danh'):
                buckets['danh'].append(img)
            elif lname.startswith('skill1') or 'skill1' in lname or lname.startswith('skil1'):
                buckets['skill1'].append(img)
            elif lname.startswith('skill2') or 'skill2' in lname or lname.startswith('skil2'):
                buckets['skill2'].append(img)
            elif lname.startswith('skill3') or 'skill3' in lname or lname.startswith('skil3'):
                buckets['skill3'].append(img)
            elif lname.startswith('chet'):
                buckets['chet'].append(img)
            else:
                buckets['dung'].append(img)

        # choose default frame
        first = None
        for k in ('dung', 'danh'):
            if buckets.get(k):
                first = buckets[k][0]
                break
        if not first:
            first = pygame.Surface((96, 96), pygame.SRCALPHA)
            pygame.draw.circle(first, (100, 0, 150), (48, 48), 44)

        self.image = first
        self.rect = self.image.get_rect(center=vi_tri)

        # animation frames
        self.idle_frames = buckets.get('dung', [])
        self.attack_frames = buckets.get('danh', [])
        self.skill1_frames = buckets.get('skill1', [])
        self.skill2_frames = buckets.get('skill2', [])
        self.skill3_frames = buckets.get('skill3', [])
        self.death_frames = buckets.get('chet', [])

        # animation control
        self.state = 'dung'
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.12
        self.death_started = False
        self.death_hold = 0.5

        self.muc_tieu = muc_tieu
        self.nhom_tat_ca = nhom_tat_ca
        self.nhom_dan = nhom_dan
        self.enemies_group = None

        # stats
        self.hp = 15
        self.hp_toi_da = 15
        self.is_boss = True

        # attack (burst)
        self.attack_interval = 3.0
        self.attack_timer = self.attack_interval
        self.burst_shots = 3
        self.burst_remaining = 0
        self.burst_shot_interval = 0.12
        self.burst_shot_timer = 0.0

        # skill2 (radial volley)
        self.skill2_interval = 12.0
        self.skill2_timer = self.skill2_interval
        self.skill2_count = 10

        # skill3 (lightning strikes - sam set)
        self.skill3_interval = 16.0
        self.skill3_timer = self.skill3_interval
        self.skill3_count = 6
        self.set_state('dung')
        self.last_touch_ticks = -999999  # Khởi tạo để va chạm có thể xảy ra ngay

    def update(self, dt, vat_cans=None):
        # Respect timestop freeze
        try:
            now = pygame.time.get_ticks()
            if getattr(self, 'freeze_end', 0) > now:
                return
        except Exception:
            pass

        # Stationary: always stay centered (in case of minor shift)
        try:
            # clamp to playable center area
            v = pygame.Rect(
                MAP_PLAYABLE_LEFT,
                MAP_PLAYABLE_TOP,
                MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
                MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
            )
            self.rect.clamp_ip(v)
        except Exception:
            pass

        # Handle burst attack if currently firing
        if self.burst_remaining > 0:
            self.burst_shot_timer -= dt
            if self.burst_shot_timer <= 0:
                self._fire_single_shot()
                self.burst_remaining -= 1
                self.burst_shot_timer = self.burst_shot_interval

        # Update animation each tick
        try:
            self.update_animation(dt)
        except Exception:
            pass

        # Advance main timers
        self.attack_timer -= dt
        self.skill2_timer -= dt
        self.skill3_timer -= dt

        # Trigger main burst attack
        if self.attack_timer <= 0 and self.burst_remaining == 0:
            # start burst
            self.burst_remaining = self.burst_shots
            self.burst_shot_timer = 0.0
            self.attack_timer = self.attack_interval
            # play attack animation
            self.set_state('danh')

        # Trigger skill2 radial volley
        if self.skill2_timer <= 0:
            self.set_state('skill2')
            self._do_skill2()
            self.skill2_timer = self.skill2_interval

        # Trigger skill3 falling bombs
        if self.skill3_timer <= 0:
            self.set_state('skill3')
            self._do_skill3()
            self.skill3_timer = self.skill3_interval

    def _fire_single_shot(self):
        # simple shot aimed at player
        if not self.muc_tieu:
            return
        origin = pygame.Vector2(self.rect.center)
        target = pygame.Vector2(self.muc_tieu.rect.center)
        dirv = target - origin
        if dirv.length() == 0:
            dirv = pygame.Vector2(1, 0)
        else:
            dirv = dirv.normalize()
        try:
            b = Bullet(self.rect.center, dirv, owner='boss3')
            if self.nhom_tat_ca is not None:
                self.nhom_tat_ca.add(b)
            if self.nhom_dan is not None:
                self.nhom_dan.add(b)
        except Exception:
            pass
        # if burst finished, return to idle state
        if self.burst_remaining == 0:
            self.set_state('dung')

    def _do_skill2(self):
        # radial volley: spawn bullets around boss and shoot outwards straight
        origin = pygame.Vector2(self.rect.center)
        n = max(1, int(self.skill2_count))
        for i in range(n):
            ang = (360.0 / n) * i
            # position slightly offset around boss circle
            offset = pygame.Vector2(math.cos(math.radians(ang)), math.sin(math.radians(ang))) * 28
            pos = origin + offset
            dirv = offset.normalize()
            try:
                b = Bullet((int(pos.x), int(pos.y)), dirv, owner='boss3')
                if self.nhom_tat_ca is not None:
                    self.nhom_tat_ca.add(b)
                if self.nhom_dan is not None:
                    self.nhom_dan.add(b)
            except Exception:
                pass
        # skill2 animation will be played once; after calling set_state above, update_animation handles returning to idle

    def _do_skill3(self):
        # Goi sam set xung quanh boss 3 (ngau nhien trong vong tron co ban kinh)
        boss_x, boss_y = self.rect.center
        radius_min = 100  # Khoang cach toi thieu tu boss
        radius_max = 250  # Khoang cach toi da tu boss
        
        for i in range(self.skill3_count):
            # Goc ngau nhien
            angle = random.uniform(0, 2 * math.pi)
            # Khoang cach ngau nhien
            distance = random.uniform(radius_min, radius_max)
            
            # Tinh toa do
            x = boss_x + distance * math.cos(angle)
            y = boss_y + distance * math.sin(angle)
            
            # Cam trong playable area
            x = max(MAP_PLAYABLE_LEFT, min(MAP_PLAYABLE_RIGHT, x))
            y = max(MAP_PLAYABLE_TOP, min(MAP_PLAYABLE_BOTTOM, y))
            
            try:
                # Tao hieu ung set
                lightning = LightningEffect(x, y, self.nhom_tat_ca, owner_boss=self, damage=2, radius=60)
                if self.nhom_tat_ca is not None:
                    self.nhom_tat_ca.add(lightning)
            except Exception:
                pass

    # Animation helpers
    def set_state(self, s):
        if s == self.state:
            return
        # don't override dead
        if getattr(self, 'state', None) == 'dead' and s != 'dead':
            return
        self.state = s
        self.frame_index = 0
        self.frame_timer = 0.0

    def update_animation(self, dt):
        # select frame list
        frames = None
        if self.state == 'dung':
            frames = self.idle_frames if self.idle_frames else [self.image]
        elif self.state == 'danh':
            frames = self.attack_frames if self.attack_frames else [self.image]
        elif self.state == 'skill1':
            frames = self.skill1_frames if self.skill1_frames else [self.image]
        elif self.state == 'skill2':
            frames = self.skill2_frames if self.skill2_frames else [self.image]
        elif self.state == 'skill3':
            frames = self.skill3_frames if self.skill3_frames else [self.image]
        elif self.state == 'dead':
            frames = self.death_frames if self.death_frames else [self.image]
        else:
            frames = [self.image]

        if not frames:
            return

        self.frame_timer += dt
        if self.state == 'dead':
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                if self.frame_index < len(frames) - 1:
                    self.frame_index += 1
                else:
                    if not self.death_started:
                        self.death_started = True
                        self.death_hold_timer = 0.0
                    else:
                        self.death_hold_timer += self.frame_duration
                    if self.death_hold_timer >= self.death_hold:
                        try:
                            self.kill()
                        except Exception:
                            pass
        else:
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % len(frames)

        # when one-shot animations finish, return to idle
        if self.state in ('skill1', 'skill2', 'skill3', 'danh'):
            # if we're on the last frame and the timer is small, treat as finished
            if self.frame_index == len(frames) - 1 and self.frame_timer < 1e-6:
                self.set_state('dung')

        try:
            self.image = frames[self.frame_index % len(frames)]
        except Exception:
            pass

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            try:
                self.kill()
            except Exception:
                pass

    nhan_sat_thuong = take_damage

    def ve_thanh_mau(self, man_hinh, offset):
        if self.hp <= 0:
            return
        bar_width = 64
        bar_height = 6
        bar_x = self.rect.centerx - bar_width // 2 - offset[0]
        bar_y = self.rect.top - 18 - offset[1]
        pygame.draw.rect(man_hinh, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        current_width = int((self.hp / self.hp_toi_da) * bar_width)
        if current_width > 0:
            pygame.draw.rect(man_hinh, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))
