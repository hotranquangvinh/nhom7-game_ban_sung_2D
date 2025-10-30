# dot.py - Quản lý các đợt quái (Wave System)
import random
import pygame
from ke_thu import Enemy
from ke_thu_2 import MeleeEnemy
from ke_thu_3 import JumperEnemy
from boss import Boss
from boss2 import Boss2
from boss3 import Boss3
from che_do import difficulty

# Import quan ly am thanh
def get_sound_manager():
    try:
        from amthanh import quan_ly_am_thanh
        return quan_ly_am_thanh
    except:
        return None


class WaveManager:
    """
    Quản lý hệ thống đợt quái (wave).
    Mỗi đợt sẽ có số lượng và loại quái khác nhau.
    """
    def __init__(self, player, all_sprites, bullets_group, item_manager=None, enemies_group=None):
        """
        Khởi tạo Wave Manager
        
        Args:
            player: Đối tượng người chơi
            all_sprites: Nhóm sprite chứa tất cả đối tượng
            bullets_group: Nhóm đạn
            item_manager: Quản lý vật phẩm
        """
        self.player = player
        self.all_sprites = all_sprites
        self.bullets_group = bullets_group
        self.item_manager = item_manager
        # optional reference to the global enemy group (nhom_ke_thu)
        self.enemies_group = enemies_group
        
        # Trạng thái wave hiện tại
        self.current_wave = 0
        self.wave_active = False
        self.wave_completed = False
        self.all_waves_completed = False
        
        # Nhóm quái của wave hiện tại
        self.current_enemies = pygame.sprite.Group()
        
        # Hệ thống thông báo giữa các đợt
        self.waiting_for_next_wave = False
        self.wave_transition_timer = 0
        self.wave_transition_duration = 3.0  # 3 giây chờ giữa các đợt
        self.wave_transition_message = ""
        
        # Định nghĩa các đợt quái (theo yêu cầu mới):
        # Che do BINH THUONG: 5 waves (normal, normal+melee+jumper, boss, boss2, boss3)
        # Che do KHO: 1 wave (ca 3 boss cung luc)
        self.waves_normal = [
            {
                'name': 'Dot 1',
                'enemies': [
                    {'type': 'normal', 'count': 5, 'schedule': {'interval': 3.0, 'batch': 2}},
                ]
            },
            {
                'name': 'Dot 2',
                'enemies': [
                    {'type': 'normal', 'count': 2},
                    {'type': 'melee', 'count': 3, 'schedule': {'interval': 4.0, 'batch': 1}},
                    {'type': 'jumper', 'count': 2, 'schedule': {'interval': 5.0, 'batch': 1}},
                ]
            },
            {
                'name': 'Dot 3 (Boss)',
                'enemies': [
                    {'type': 'boss', 'count': 1},
                ]
            },
            {
                'name': 'Dot 4 (Boss2)',
                'enemies': [
                    {'type': 'boss2', 'count': 1},
                ]
            },
            {
                'name': 'Dot 5 (Boss3)',
                'enemies': [
                    {'type': 'boss3', 'count': 1},
                ]
            },
        ]
        
        # Che do KHO: Chi co 1 dot voi ca 3 boss xuat hien cung luc
        self.waves_hard = [
            {
                'name': 'Dot 1 (Ca 3 boss)',
                'enemies': [
                    {'type': 'boss', 'count': 1},
                    {'type': 'boss2', 'count': 1},
                    {'type': 'boss3', 'count': 1},
                ]
            },
        ]
        
        # Chon waves dua tren che do
        if difficulty.is_hard_mode():
            self.waves = self.waves_hard
        else:
            self.waves = self.waves_normal

        # Scheduled spawn state (per-wave)
        # pending_spawns: { 'normal': remaining_count, ... }
        self.pending_spawns = {}
        # spawn_timers: { 'normal': accumulator_seconds, ... }
        self.spawn_timers = {}
        # spawn_schedules: { 'normal': {'interval':float,'batch':int}, ... }
        self.spawn_schedules = {}
        # Small grace period after wave start before allowing completion checks
        self.completion_grace_time = 0.15  # seconds
        self.completion_grace_timer = 0.0
        # Track boss-specific state so we don't accidentally mark a boss-wave complete
        # before the boss entity is actually present on the map.
        self.current_wave_has_boss = False
        self.boss_spawn_attempted = False
    
    def start_wave(self, wave_number):
        """
        Bắt đầu một đợt quái
        
        Args:
            wave_number: Số thứ tự đợt (0-indexed)
        """
        if wave_number >= len(self.waves):
            self.all_waves_completed = True
            return
        
        self.current_wave = wave_number
        self.wave_active = True
        self.wave_completed = False
        # set grace timer so we don't immediately mark wave complete
        self.completion_grace_timer = self.completion_grace_time
        
        # Xóa quái cũ (nếu có)
        self.current_enemies.empty()

        # Reset scheduled spawn trackers
        self.pending_spawns.clear()
        self.spawn_timers.clear()
        self.spawn_schedules.clear()

        # Spawn quái theo cấu hình wave
        wave_config = self.waves[wave_number]
        # detect if this wave contains a boss so we can treat completion carefully
        self.current_wave_has_boss = any(
            (entry.get('type') in ('boss', 'boss2', 'boss3') and entry.get('count', 0) > 0)
            for entry in wave_config.get('enemies', [])
        )
        # reset boss spawn tracking for this wave
        self.boss_spawn_attempted = False
        # if this is a boss wave, give a longer grace timer so spawn_protection and
        # animations have time before any completion logic runs
        if self.current_wave_has_boss:
            self.completion_grace_timer = max(self.completion_grace_timer, 1.0)
            # Phat nhac boss khi bat dau song boss (chi o che do thuong, che do kho da phat tu dau)
            try:
                from che_do import difficulty
                sound_mgr = get_sound_manager()
                if sound_mgr and not difficulty.is_hard_mode():
                    sound_mgr.play_nhac_boss()
            except Exception:
                pass
        print(f"Bắt đầu {wave_config['name']}")

        for enemy_group in wave_config['enemies']:
            enemy_type = enemy_group['type']
            count = enemy_group.get('count', 0)
            schedule = enemy_group.get('schedule')

            if schedule and isinstance(schedule, dict):
                # register for scheduled spawning
                self.pending_spawns[enemy_type] = count
                self.spawn_timers[enemy_type] = 0.0
                self.spawn_schedules[enemy_type] = {
                    'interval': float(schedule.get('interval', 1.0)),
                    'batch': int(schedule.get('batch', 1)),
                }
                # If batch > 0 and we want an immediate spawn at wave start, spawn one batch now
                initial_batch = self.spawn_schedules[enemy_type].get('batch', 1)
                if initial_batch > 0:
                    spawn_now = min(initial_batch, self.pending_spawns.get(enemy_type, 0))
                    for _ in range(spawn_now):
                        self._spawn_enemy(enemy_type)
                    self.pending_spawns[enemy_type] = max(0, self.pending_spawns.get(enemy_type, 0) - spawn_now)
            else:
                # spawn all immediately for non-scheduled entries
                for _ in range(count):
                    self._spawn_enemy(enemy_type)

        # Debug: print pending spawn state after initial spawns
        try:
            print(f"[WaveManager] after start_wave pending_spawns={self.pending_spawns}, current_count={len(self.current_enemies)}")
        except Exception:
            pass
    
    def _spawn_enemy(self, enemy_type):
        """
        Spawn một kẻ thù tại vị trí ngẫu nhiên
        
        Args:
            enemy_type: Loại kẻ thù ('normal', 'melee', 'jumper', 'boss')
        """
        # Lấy kích thước map từ pygame display hoặc dùng giá trị mặc định
        try:
            from cau_hinh import MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, MAP_PLAYABLE_RIGHT, MAP_PLAYABLE_BOTTOM
            map_left = MAP_PLAYABLE_LEFT
            map_top = MAP_PLAYABLE_TOP
            map_right = MAP_PLAYABLE_RIGHT
            map_bottom = MAP_PLAYABLE_BOTTOM
        except:
            map_left = 0
            map_top = 0
            map_right = 2000
            map_bottom = 1666
        
        # Spawn ở các cạnh của map (ngoài màn hình)
        side = random.choice(['top', 'bottom', 'left', 'right'])
        
        if side == 'top':
            x = random.randint(map_left, map_right)
            y = map_top
        elif side == 'bottom':
            x = random.randint(map_left, map_right)
            y = map_bottom
        elif side == 'left':
            x = map_left
            y = random.randint(map_top, map_bottom)
        else:  # right
            x = map_right
            y = random.randint(map_top, map_bottom)
        
        position = (x, y)

        # Nếu là boss (bất kỳ loại), spawn ở giữa vùng chơi cho rõ ràng (đợt boss)
        if enemy_type in ('boss', 'boss2', 'boss3'):
            try:
                from cau_hinh import MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, MAP_PLAYABLE_RIGHT, MAP_PLAYABLE_BOTTOM
                cx = (MAP_PLAYABLE_LEFT + MAP_PLAYABLE_RIGHT) // 2
                cy = (MAP_PLAYABLE_TOP + MAP_PLAYABLE_BOTTOM) // 2
                position = (cx, cy)
            except Exception:
                # fallback to previously chosen position
                pass
        
        # Tạo kẻ thù theo loại
        if enemy_type == 'normal':
            enemy = Enemy(position, self.player, self.all_sprites, self.bullets_group, self.item_manager)
        elif enemy_type == 'melee':
            enemy = MeleeEnemy(position, self.player, self.all_sprites, self.item_manager)
        elif enemy_type == 'jumper':
            enemy = JumperEnemy(position, self.player, self.all_sprites, self.item_manager)
        elif enemy_type == 'boss':
            # Boss constructor expects (vi_tri, muc_tieu, nhom_tat_ca, nhom_dan=None)
            # pass bullets_group as nhom_dan
            enemy = Boss(position, self.player, self.all_sprites, self.bullets_group)
            # Tang HP trong che do kho
            if difficulty.is_hard_mode():
                enemy.hp *= 2
                enemy.hp_toi_da *= 2
        elif enemy_type == 'boss2':
            # Boss2 (melee boss) expects same constructor signature
            enemy = Boss2(position, self.player, self.all_sprites, self.bullets_group)
            # Tang HP trong che do kho
            if difficulty.is_hard_mode():
                enemy.hp *= 2
                enemy.hp_toi_da *= 2
            # If boss spawns overlapping the player, move it away so it isn't immediately removed by collision code
            try:
                if self.player and hasattr(self.player, 'rect') and enemy.rect.colliderect(self.player.rect):
                    # offset boss to the right or left depending on space
                    safe_offset = 200
                    # try to place to the right
                    new_x = enemy.rect.x + safe_offset
                    new_y = enemy.rect.y
                    # clamp within playable area
                    from cau_hinh import MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, MAP_PLAYABLE_RIGHT, MAP_PLAYABLE_BOTTOM
                    min_x = MAP_PLAYABLE_LEFT
                    max_x = MAP_PLAYABLE_RIGHT - enemy.rect.width
                    min_y = MAP_PLAYABLE_TOP
                    max_y = MAP_PLAYABLE_BOTTOM - enemy.rect.height
                    if new_x > max_x:
                        new_x = enemy.rect.x - safe_offset
                    # final clamp
                    new_x = max(min_x, min(new_x, max_x))
                    new_y = max(min_y, min(new_y, max_y))
                    enemy.rect.topleft = (new_x, new_y)
            except Exception:
                pass
        elif enemy_type == 'boss3':
            # Boss3 (stationary center boss)
            enemy = Boss3(position, self.player, self.all_sprites, self.bullets_group)
            # Tang HP trong che do kho
            if difficulty.is_hard_mode():
                enemy.hp *= 2
                enemy.hp_toi_da *= 2
            # If boss spawns overlapping the player, move it away so it isn't immediately removed by collision code
            try:
                if self.player and hasattr(self.player, 'rect') and enemy.rect.colliderect(self.player.rect):
                    safe_offset = 200
                    new_x = enemy.rect.x + safe_offset
                    new_y = enemy.rect.y
                    from cau_hinh import MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, MAP_PLAYABLE_RIGHT, MAP_PLAYABLE_BOTTOM
                    min_x = MAP_PLAYABLE_LEFT
                    max_x = MAP_PLAYABLE_RIGHT - enemy.rect.width
                    min_y = MAP_PLAYABLE_TOP
                    max_y = MAP_PLAYABLE_BOTTOM - enemy.rect.height
                    if new_x > max_x:
                        new_x = enemy.rect.x - safe_offset
                    new_x = max(min_x, min(new_x, max_x))
                    new_y = max(min_y, min(new_y, max_y))
                    enemy.rect.topleft = (new_x, new_y)
            except Exception:
                pass

        else:
            # Mặc định tạo enemy thường
            enemy = Enemy(position, self.player, self.all_sprites, self.bullets_group, self.item_manager)
        
        # Debug: log boss spawn for any boss type and mark we've attempted/spawned the boss
        try:
            if enemy_type in ('boss', 'boss2', 'boss3'):
                print(f"[WaveManager] Spawned {enemy_type} at {position}, final rect {getattr(enemy,'rect',None)}")
                # Give boss a short spawn protection window to avoid instant death/race conditions
                try:
                    setattr(enemy, 'spawn_protection', 1.0)
                    print(f"[WaveManager] {enemy_type} spawn_protection set to 1.0s")
                except Exception:
                    pass
                # mark that we've attempted/spawned the boss for this wave
                try:
                    self.boss_spawn_attempted = True
                except Exception:
                    pass
        except Exception:
            pass

        # Thêm vào nhóm
        self.current_enemies.add(enemy)
        self.all_sprites.add(enemy)
        # Nếu được truyền nhóm kẻ thù chung, thêm vào để tương thích với phần còn lại của game
        try:
            if self.enemies_group is not None:
                # add to global enemy group
                self.enemies_group.add(enemy)
                # also attach reference so boss can spawn minions into the same group
                try:
                    setattr(enemy, 'enemies_group', self.enemies_group)
                except Exception:
                    pass
        except Exception:
            pass
    
    def update(self):
        """
        Cập nhật trạng thái wave
        """
        # Nếu đang chờ đợt tiếp theo
        if self.waiting_for_next_wave:
            self.wave_transition_timer -= 1/60  # Giả sử game chạy 60 FPS
            
            if self.wave_transition_timer <= 0:
                # Hết thời gian chờ, bắt đầu đợt mới
                self.waiting_for_next_wave = False
                next_wave = self.current_wave + 1
                if next_wave < len(self.waves):
                    self.start_wave(next_wave)
                else:
                    self.all_waves_completed = True
                    self.wave_transition_message = "Hoan thanh tat ca cac dot!"
                    print("Da hoan thanh tat ca cac dot quai!")
            return
        
        if not self.wave_active:
            return

        # If we're still in the start-up grace period, advance the timer and skip completion checks
        if self.completion_grace_timer > 0:
            self.completion_grace_timer = max(0.0, self.completion_grace_timer - (1.0/60.0))

        # First: process scheduled spawns
        for etype, remaining in list(self.pending_spawns.items()):
            if remaining <= 0:
                # nothing left to spawn for this type
                self.pending_spawns.pop(etype, None)
                self.spawn_timers.pop(etype, None)
                self.spawn_schedules.pop(etype, None)
                continue

            # advance timer
            # update() is called without dt; assume 60 FPS => dt ~= 1/60
            timer = self.spawn_timers.get(etype, 0.0) + (1.0 / 60.0)
            schedule = self.spawn_schedules.get(etype, {'interval': 1.0, 'batch': 1})
            interval = schedule.get('interval', 1.0)
            batch = schedule.get('batch', 1)

            if timer >= interval:
                # spawn up to `batch` of this type
                to_spawn = min(batch, self.pending_spawns.get(etype, 0))
                for _ in range(to_spawn):
                    self._spawn_enemy(etype)
                self.pending_spawns[etype] = max(0, self.pending_spawns.get(etype, 0) - to_spawn)
                timer = 0.0

            self.spawn_timers[etype] = timer

        # Kiểm tra xem còn quái nào sống không (chỉ tính những enemy đã spawn ra)
        # Treat boss entities as "alive" until their death animation fully finishes
        alive_enemies = [
            e for e in self.current_enemies
            if (getattr(e, 'hp', 0) > 0) or (getattr(e, 'is_boss', False) and not getattr(e, 'death_started', False))
        ]

        # If this wave is supposed to contain a boss but we haven't actually
        # spawned it (edge cases where spawn was skipped), force a spawn now
        # and skip completion detection for this frame. Detect the actual boss
        # type defined in the current wave (boss, boss2, boss3).
        if self.current_wave_has_boss and not self.boss_spawn_attempted:
            try:
                # determine which boss type is defined for this wave
                boss_type = None
                for entry in self.waves[self.current_wave].get('enemies', []):
                    t = entry.get('type')
                    if t in ('boss', 'boss2', 'boss3') and entry.get('count', 0) > 0:
                        boss_type = t
                        break
                if boss_type:
                    self._spawn_enemy(boss_type)
                    self.boss_spawn_attempted = True
                    return
            except Exception:
                pass

        # Wave hoàn thành chỉ khi không còn quái sống và không còn pending spawns
        # but only after the initial grace period has expired
        pending_remaining = sum(self.pending_spawns.values()) if self.pending_spawns else 0
        if self.completion_grace_timer <= 0.0 and len(alive_enemies) == 0 and pending_remaining == 0:
            # Wave hoàn thành
            self.wave_completed = True
            self.wave_active = False
            print(f"Hoan thanh dot {self.current_wave + 1}!")

            # Kiem tra xem co dot tiep theo khong
            next_wave = self.current_wave + 1
            if next_wave < len(self.waves):
                # Co dot tiep theo - hien thi thong bao
                self.waiting_for_next_wave = True
                self.wave_transition_timer = self.wave_transition_duration
                next_wave_name = self.waves[next_wave]['name']
                self.wave_transition_message = f"Chuan bi {next_wave_name}..."
                print(f"Chuan bi {next_wave_name}...")
            else:
                # Khong con dot nao - nhung cho mot chut truoc khi hien thi thong bao hoan thanh
                # de nguoi choi co the thay boss chet
                self.waiting_for_next_wave = True
                self.wave_transition_timer = 2.0  # Cho 2 giay sau khi boss chet
                self.wave_transition_message = "Hoan thanh tat ca cac dot!"
                print("Da hoan thanh tat ca cac dot quai!")
    
    def next_wave(self):
        """
        Chuyen sang dot tiep theo (DEPRECATED - gio tu dong chuyen trong update)
        """
        # Ham nay giu lai de tuong thich nhung khong can thiet nua
        # Vi update() tu dong chuyen dot
        pass
    
    def update_with_dt(self, dt):
        """
        Cập nhật với delta time chính xác
        
        Args:
            dt: Delta time (giây)
        """
        # Nếu đang chờ đợt tiếp theo
        if self.waiting_for_next_wave:
            self.wave_transition_timer -= dt
            
            if self.wave_transition_timer <= 0:
                # Hết thời gian chờ
                self.waiting_for_next_wave = False
                next_wave = self.current_wave + 1
                if next_wave < len(self.waves):
                    # Bắt đầu đợt mới
                    self.start_wave(next_wave)
                else:
                    # Đã hết tất cả các đợt - hiển thị thông báo hoàn thành
                    self.all_waves_completed = True
                    print("Hiển thị thông báo hoàn thành tất cả các đợt!")
            return
        
        if not self.wave_active:
            return
        # If we're still in the start-up grace period, advance the timer and skip completion checks
        if self.completion_grace_timer > 0:
            self.completion_grace_timer = max(0.0, self.completion_grace_timer - dt)

        # Process scheduled spawns using provided dt
        for etype, remaining in list(self.pending_spawns.items()):
            if remaining <= 0:
                self.pending_spawns.pop(etype, None)
                self.spawn_timers.pop(etype, None)
                self.spawn_schedules.pop(etype, None)
                continue

            timer = self.spawn_timers.get(etype, 0.0) + dt
            schedule = self.spawn_schedules.get(etype, {'interval': 1.0, 'batch': 1})
            interval = schedule.get('interval', 1.0)
            batch = schedule.get('batch', 1)

            if timer >= interval:
                to_spawn = min(batch, self.pending_spawns.get(etype, 0))
                for _ in range(to_spawn):
                    self._spawn_enemy(etype)
                self.pending_spawns[etype] = max(0, self.pending_spawns.get(etype, 0) - to_spawn)
                timer = 0.0

            self.spawn_timers[etype] = timer

        # Kiểm tra xem còn quái nào sống không (chỉ tính những enemy đã spawn ra)
        # Treat boss entities as "alive" until their death animation fully finishes
        alive_enemies = [
            e for e in self.current_enemies
            if (getattr(e, 'hp', 0) > 0) or (getattr(e, 'is_boss', False) and not getattr(e, 'death_started', False))
        ]

        # If this wave expects a boss but we haven't spawned it yet, try to spawn
        # now and skip completion checks for this update tick.
        if self.current_wave_has_boss and not self.boss_spawn_attempted:
            try:
                # determine which boss type is defined for this wave
                boss_type = None
                for entry in self.waves[self.current_wave].get('enemies', []):
                    t = entry.get('type')
                    if t in ('boss', 'boss2', 'boss3') and entry.get('count', 0) > 0:
                        boss_type = t
                        break
                if boss_type:
                    self._spawn_enemy(boss_type)
                    self.boss_spawn_attempted = True
                    return
            except Exception:
                pass

        pending_remaining = sum(self.pending_spawns.values()) if self.pending_spawns else 0
        if self.completion_grace_timer <= 0.0 and len(alive_enemies) == 0 and pending_remaining == 0:
            # Wave hoàn thành
            self.wave_completed = True
            self.wave_active = False
            print(f"Hoan thanh dot {self.current_wave + 1}!")

            # Kiem tra xem co dot tiep theo khong
            next_wave = self.current_wave + 1
            if next_wave < len(self.waves):
                # Co dot tiep theo - hien thi thong bao
                self.waiting_for_next_wave = True
                self.wave_transition_timer = self.wave_transition_duration
                next_wave_name = self.waves[next_wave]['name']
                self.wave_transition_message = f"Chuan bi {next_wave_name}..."
                print(f"Chuan bi {next_wave_name}...")
            else:
                # Khong con dot nao - nhung cho mot chut truoc khi hien thi thong bao hoan thanh
                # de nguoi choi co the thay boss chet
                self.waiting_for_next_wave = True
                self.wave_transition_timer = 2.0  # Cho 2 giay sau khi boss chet
                self.wave_transition_message = "Hoan thanh tat ca cac dot!"
                print("Da hoan thanh tat ca cac dot quai!")
    
    def get_current_wave_info(self):
        """
        Lay thong tin ve wave hien tai
        
        Returns:
            dict: Thong tin wave (so wave, ten, so quai con lai)
        """
        if self.all_waves_completed:
            return {
                'wave_number': self.current_wave + 1,
                'wave_name': 'Hoan thanh',
                'enemies_remaining': 0,
                'total_enemies': 0,
                'waiting_for_next': False,
                'transition_message': self.wave_transition_message,
                'transition_time_left': 0,
            }
        
        alive_enemies = [e for e in self.current_enemies if e.hp > 0]
        total_enemies = len(self.current_enemies)
        
        wave_name = self.waves[self.current_wave]['name'] if self.current_wave < len(self.waves) else 'Unknown'
        
        return {
            'wave_number': self.current_wave + 1,
            'wave_name': wave_name,
            'enemies_remaining': len(alive_enemies),
            'total_enemies': total_enemies,
            'waiting_for_next': self.waiting_for_next_wave,
            'transition_message': self.wave_transition_message,
            'transition_time_left': max(0, self.wave_transition_timer),
        }

    def current_wave_has_type(self, enemy_type: str) -> bool:
        """
        Kiểm tra xem wave hiện tại có loại kẻ thù `enemy_type` hay không.

        Args:
            enemy_type: 'normal' | 'melee' | 'jumper' | 'boss'

        Returns:
            bool: True nếu wave hiện tại định nghĩa loại đó và số lượng > 0.
        """
        try:
            if self.current_wave >= len(self.waves):
                return False
            for entry in self.waves[self.current_wave]['enemies']:
                if entry.get('type') == enemy_type and entry.get('count', 0) > 0:
                    return True
        except Exception:
            pass
        return False
    
    def reset(self):
        """
        Reset wave manager về trạng thái ban đầu
        """
        self.current_wave = 0
        self.wave_active = False
        self.wave_completed = False
        self.all_waves_completed = False
        self.current_enemies.empty()
        self.waiting_for_next_wave = False
        self.wave_transition_timer = 0
        self.wave_transition_message = ""
    
    def draw_transition_message(self, screen, font):
        """
        Vẽ thông báo chuyển đợt lên màn hình
        
        Args:
            screen: Pygame surface để vẽ
            font: Pygame font để render text
        """
        if not self.waiting_for_next_wave and not self.all_waves_completed:
            return
        
        # Lấy kích thước màn hình
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Tạo nền mờ
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Vẽ text thông báo
        if self.waiting_for_next_wave:
            # Thông báo chuyển đợt
            message = self.wave_transition_message
            time_left = int(self.wave_transition_timer) + 1
            countdown_text = f"{time_left}"
            
            # Text chính
            text_surface = font.render(message, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 30))
            screen.blit(text_surface, text_rect)
            
            # Countdown
            try:
                big_font = pygame.font.Font(None, 100)
                countdown_surface = big_font.render(countdown_text, True, (255, 255, 0))
                countdown_rect = countdown_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 40))
                screen.blit(countdown_surface, countdown_rect)
            except:
                # Nếu không tạo được font lớn, dùng font thường
                countdown_surface = font.render(countdown_text, True, (255, 255, 0))
                countdown_rect = countdown_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 40))
                screen.blit(countdown_surface, countdown_rect)
        
        elif self.all_waves_completed:
            # Thông báo hoàn thành (đã được kiểm tra trong update)
            text_surface = font.render(self.wave_transition_message, True, (0, 255, 0))
            text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(text_surface, text_rect)
