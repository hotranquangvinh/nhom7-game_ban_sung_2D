import os
import random
import math
import pygame
from cau_hinh import (
    ENEMY_SPEED,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
)
from ke_thu_2 import MeleeEnemy
from ke_thu_3 import JumperEnemy
from dan import Bullet


class Boss2(pygame.sprite.Sprite):
    """
    Boss2: melee boss.
    - HP: 10
    - Skill1 (every 10s): summon 2 MeleeEnemy and 3 JumperEnemy near the boss
    - Skill2 (every 6s): fire 3 enemy bullets in a spread
    """
    def __init__(self, vi_tri, muc_tieu, nhom_tat_ca, nhom_dan=None):
        super().__init__()
        # Load animation frames from assets/boss2 grouped by prefix
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'boss2')
        buckets = {
            'dung': [],
            'di': [],
            'trungdan': [],
            'danh': [],
            'skill1': [],
            'skill2': [],
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
                # optional scaling: keep native size
            except Exception:
                continue

            # bucket by likely prefixes (accepting common typos like 'skil')
            if lname.startswith('dung'):
                buckets['dung'].append(img)
            elif lname.startswith('di'):
                buckets['di'].append(img)
            elif lname.startswith('trungdan') or 'trungdan' in lname:
                buckets['trungdan'].append(img)
            elif lname.startswith('danh') or 'danh' in lname:
                buckets['danh'].append(img)
            elif lname.startswith('skill1_') or lname.startswith('skil1_') or 'skill1' in lname or 'skil1' in lname:
                buckets['skill1'].append(img)
            elif lname.startswith('skill2_') or lname.startswith('skil2_') or 'skill2' in lname or 'skil2' in lname:
                buckets['skill2'].append(img)
            elif lname.startswith('chet') or 'chet' in lname:
                buckets['chet'].append(img)
            else:
                # fallback to idle/standing
                buckets['dung'].append(img)

        # choose sensible default first frame
        first = None
        for key in ('dung', 'di', 'danh'):
            if buckets.get(key):
                first = buckets[key][0]
                break
        if not first:
            first = pygame.Surface((90, 90), pygame.SRCALPHA)
            first.fill((180, 30, 30))

        self.image = first
        self.rect = self.image.get_rect(center=vi_tri)

        # animation buckets attached
        self.idle_frames = buckets.get('dung', [])
        self.move_frames = buckets.get('di', [])
        self.hit_frames = buckets.get('trungdan', [])
        self.attack_frames = buckets.get('danh', [])
        self.skill1_frames = buckets.get('skill1', [])
        self.skill2_frames = buckets.get('skill2', [])
        self.death_frames = buckets.get('chet', [])

        # animation control
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.12
        self._hit_playing = False
        self.death_started = False
        # facing direction (used to flip sprite horizontally)
        self.direction = pygame.Vector2(1, 0)

        # References
        self.muc_tieu = muc_tieu
        self.nhom_tat_ca = nhom_tat_ca
        # group for enemy bullets (nhom_dan) — may be None
        self.nhom_dan = nhom_dan

        # Optional link to the main enemy group (set by WaveManager after spawn)
        self.enemies_group = None

        # Stats
        self.hp = 10
        self.hp_toi_da = 10
        self.speed = ENEMY_SPEED * 0.9
        self.is_boss = True
        self.is_melee = True

        # Movement / simple melee behaviour
        self.state = 'spawn_idle'
        self.state_timer = 0.0
        self.idle_time = 1.0

        # Skill timers
        self.skill1_interval = 10.0
        self.skill1_timer = self.skill1_interval

        self.skill2_interval = 6.0
        self.skill2_timer = self.skill2_interval

        # Skill parameters
        self.skill1_spawn_counts = {'melee': 2, 'jumper': 3}
        self.skill2_bullets = 3
        self.skill2_spread_deg = 20

        # Visual / animation placeholders
        # death_started defined above as animation control
        self.last_touch_ticks = -999999  # Khởi tạo để va chạm có thể xảy ra ngay

    def update(self, dt, vat_cans=None):
        # Respect timestop freeze
        try:
            now_ms = pygame.time.get_ticks()
            if getattr(self, 'freeze_end', 0) > now_ms:
                return
        except Exception:
            pass

        # simple idle -> melee roam behaviour (if player nearby)
        self.state_timer += dt
        if self.state == 'spawn_idle' and self.state_timer >= self.idle_time:
            self.state = 'roam'
            self.state_timer = 0.0

        if self.state == 'roam' and self.muc_tieu:
            vec = pygame.Vector2(self.muc_tieu.rect.center) - pygame.Vector2(self.rect.center)
            dist = vec.length()
            if dist > 0:
                dirn = vec.normalize()
                # update facing direction so animations can be flipped
                try:
                    self.direction = dirn
                except Exception:
                    pass
                # move only when a bit far from player (melee closes gap)
                if dist > 50:
                    dx = dirn.x * self.speed * dt
                    dy = dirn.y * self.speed * dt
                    try:
                        self.rect.x += dx
                        self.rect.y += dy
                    except Exception:
                        pass

        # clamp inside playable area
        try:
            v = pygame.Rect(
                MAP_PLAYABLE_LEFT,
                MAP_PLAYABLE_TOP,
                MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
                MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
            )
            self.rect.clamp_ip(v)
        except Exception:
            pass

        # Advance skill timers
        self.skill1_timer -= dt
        self.skill2_timer -= dt

        # If skill triggers, switch to skill state so animation can play
        if self.skill1_timer <= 0:
            # set skill1 state so animation can play
            self.set_state('skill1')
            self._do_skill1()
            self.skill1_timer = self.skill1_interval

        if self.skill2_timer <= 0:
            self.set_state('skill2')
            self._do_skill2()
            self.skill2_timer = self.skill2_interval

        # Update animation after logic
        try:
            self.update_animation(dt)
        except Exception:
            pass

    def _do_skill1(self):
        """Summon minions near the boss: 2 melee (MeleeEnemy) and 3 jumper (JumperEnemy)."""
        spawned = []
        origin = pygame.Vector2(self.rect.center)
        # spawn melee
        for i in range(self.skill1_spawn_counts.get('melee', 0)):
            off = pygame.Vector2(random.randint(-60, 60), random.randint(-60, 60))
            pos = (int(origin.x + off.x), int(origin.y + off.y))
            try:
                m = MeleeEnemy(pos, self.muc_tieu, self.nhom_tat_ca)
                spawned.append(m)
                self.nhom_tat_ca.add(m)
                if getattr(self, 'enemies_group', None) is not None:
                    try:
                        self.enemies_group.add(m)
                    except Exception:
                        pass
            except Exception:
                pass

        # spawn jumper
        for i in range(self.skill1_spawn_counts.get('jumper', 0)):
            off = pygame.Vector2(random.randint(-80, 80), random.randint(-80, 80))
            pos = (int(origin.x + off.x), int(origin.y + off.y))
            try:
                j = JumperEnemy(pos, self.muc_tieu, self.nhom_tat_ca)
                spawned.append(j)
                self.nhom_tat_ca.add(j)
                if getattr(self, 'enemies_group', None) is not None:
                    try:
                        self.enemies_group.add(j)
                    except Exception:
                        pass
            except Exception:
                pass

        try:
            print(f"[Boss2] Summoned {len(spawned)} minions")
        except Exception:
            pass

    def _do_skill2(self):
        """Fire 3 bullets in a spread toward the player."""
        if not self.muc_tieu:
            return
        origin = pygame.Vector2(self.rect.center)
        target = pygame.Vector2(self.muc_tieu.rect.center)
        base = (target - origin)
        if base.length() == 0:
            base = pygame.Vector2(1, 0)
        else:
            base = base.normalize()

        mid_angle = 0
        # create spread: -spread/2, 0, +spread/2
        spans = []
        total = self.skill2_bullets
        spread = self.skill2_spread_deg
        if total == 1:
            spans = [0]
        else:
            step = spread / (total - 1)
            start = -spread / 2
            spans = [start + i * step for i in range(total)]

        for ang in spans:
            try:
                # rotate vector by ang degrees
                d = base.rotate(ang)
                vien = Bullet(self.rect.center, d, owner='boss2')
                # add to global sprite lists
                try:
                    self.nhom_tat_ca.add(vien)
                except Exception:
                    pass
                try:
                    if self.nhom_dan is not None:
                        self.nhom_dan.add(vien)
                except Exception:
                    pass
            except Exception:
                pass

        try:
            print(f"[Boss2] Fired {self.skill2_bullets} bullets")
        except Exception:
            pass

    def set_state(self, s):
        if s == self.state:
            return
        # don't change out of dead
        if getattr(self, 'state', None) == 'dead' and s != 'dead':
            return
        self.state = s
        self.frame_index = 0
        self.frame_timer = 0.0
        # hit state control
        if s == 'hit':
            self._hit_playing = True

    def update_animation(self, dt):
        # choose frames based on state
        frames = None
        if self._hit_playing and self.hit_frames:
            frames = self.hit_frames
        else:
            if self.state == 'spawn_idle' and self.idle_frames:
                frames = self.idle_frames
            elif self.state == 'roam' and self.move_frames:
                frames = self.move_frames
            elif self.state == 'attack' and self.attack_frames:
                frames = self.attack_frames
            elif self.state == 'skill1' and self.skill1_frames:
                frames = self.skill1_frames
            elif self.state == 'skill2' and self.skill2_frames:
                frames = self.skill2_frames
            elif self.state == 'dead' and self.death_frames:
                frames = self.death_frames
            else:
                frames = self.idle_frames if self.idle_frames else [self.image]

        if not frames:
            return

        self.frame_timer += dt
        # Dead: play once and then kill
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
                    if getattr(self, 'death_hold', 0.5) <= 0 or self.death_hold_timer >= getattr(self, 'death_hold', 0.5):
                        try:
                            self.kill()
                        except Exception:
                            pass
                        return
        else:
            if self.frame_timer >= self.frame_duration:
                self.frame_timer -= self.frame_duration
                self.frame_index = (self.frame_index + 1) % len(frames)

        # when skill frames finish, return to roam
        if self.state in ('skill1', 'skill2') and self.frame_index == len(frames) - 1 and self.frame_timer < 1e-6:
            # finished playing one-shot skill animation
            self.set_state('roam')

        # when hit animation ends, clear hit flag
        if self._hit_playing:
            # assume hit animation length is len(frames)
            # when last frame reached, stop hit
            if self.frame_index == len(frames) - 1 and self.frame_timer < 1e-6:
                self._hit_playing = False

        try:
            current = frames[self.frame_index % len(frames)]
            self.image = current
        except Exception:
            pass

    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            try:
                self.kill()
            except Exception:
                pass

    # Alias compatibility
    nhan_sat_thuong = take_damage

    def ve_thanh_mau(self, man_hinh, offset):
        if self.hp <= 0:
            return
        bar_width = 60
        bar_height = 6
        bar_x = self.rect.centerx - bar_width // 2 - offset[0]
        bar_y = self.rect.top - 15 - offset[1]
        pygame.draw.rect(man_hinh, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        current_width = int((self.hp / self.hp_toi_da) * bar_width)
        if current_width > 0:
            pygame.draw.rect(man_hinh, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))

