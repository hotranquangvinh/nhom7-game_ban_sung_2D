import pygame, os
from dan import Bullet
from cau_hinh import (
    PLAYER_SPEED,
    PLAYER_MAX_HP,
    PLAYER_MAGAZINE,
    PLAYER_RESERVE_MAX,
    RELOAD_TIME,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
)

# Import quan ly am thanh (tránh circular import, nên import cách động)
def get_sound_manager():
    try:
        from amthanh import quan_ly_am_thanh
        return quan_ly_am_thanh
    except:
        return None

class NguoiChoi(pygame.sprite.Sprite):
    def __init__(self, vi_tri, nhom_tat_ca, nhom_dan, hp_goc=None):
        super().__init__()

        # ===== Hàm hỗ trợ load ảnh =====
        def load_img(name):
            path = os.path.join("assets", "nguoi_choi", name)
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (80, 100))
            return img

        # ===== Load animation chạy với flip =====
        def load_chay_animation():
            animations = {}
            animations[0] = [load_img(f'chaythang{i}.png') for i in range(1, 9)]
            animations[1] = [load_img(f'chay_ngiengphai{i}.png') for i in range(1, 9)]
            animations[2] = [load_img(f'chayphai{i}.png') for i in range(1, 9)]
            animations[3] = [load_img(f'chay_phaixuong{i}.png') for i in range(1, 9)]
            animations[4] = [load_img(f'chayxuong{i}.png') for i in range(1, 9)]
            animations[5] = [pygame.transform.flip(frame, True, False) for frame in animations[3]]
            animations[6] = [pygame.transform.flip(frame, True, False) for frame in animations[2]]
            animations[7] = [pygame.transform.flip(frame, True, False) for frame in animations[1]]
            return animations

        # ===== Load animation bắn (đủ 8 hướng) =====
        def load_ban_animation():
            animations = {}
            animations[0] = [load_img(f'banthang{i}.png') for i in range(1, 9)]
            animations[1] = [load_img(f'ban_ngiengphai{i}.png') for i in range(1, 9)]
            animations[2] = [load_img(f'banphai{i}.png') for i in range(1, 9)]
            animations[3] = [load_img(f'ban_phaixuong{i}.png') for i in range(1, 9)]
            animations[4] = [load_img(f'banxuong{i}.png') for i in range(1, 9)]
            animations[5] = [load_img(f'ban_traixuong{i}.png') for i in range(1, 9)]
            animations[6] = [load_img(f'bantrai{i}.png') for i in range(1, 9)]
            animations[7] = [load_img(f'ban_traithang{i}.png') for i in range(1, 9)]
            return animations

        # ===== Load animation trúng đạn (4 hướng) =====
        def load_trungdan_animation():
            animations = {}
            animations['phai'] = [load_img(f'trungdan_phai{i}.png') for i in range(1, 3)]
            animations['trai'] = [load_img(f'trungdan_trai{i}.png') for i in range(1, 3)]
            animations['thang'] = [load_img(f'trungdan_giua{i}.png') for i in range(1, 3)]
            animations['xuong'] = [load_img(f'trungdan_duoi{i}.png') for i in range(1, 3)]
            return animations

        # ===== Load animation nhảy với flip =====
        def load_nhay_animation():
            animations = {}
            animations[0] = [load_img(f'nhaylen{i}.png') for i in range(1, 12)]
            animations[1] = [load_img(f'nhay_ngienglen{i}.png') for i in range(1, 12)]
            animations[2] = [load_img(f'nhayphai{i}.png') for i in range(1, 12)]
            animations[3] = [load_img(f'nhay_ngiengxuong{i}.png') for i in range(1, 12)]
            animations[4] = [load_img(f'nhayxuong{i}.png') for i in range(1, 12)]
            animations[5] = [pygame.transform.flip(frame, True, False) for frame in animations[3]]
            animations[6] = [pygame.transform.flip(frame, True, False) for frame in animations[2]]
            animations[7] = [pygame.transform.flip(frame, True, False) for frame in animations[1]]
            return animations

        # ===== Load toàn bộ animation =====
        self.animations = {
            'Đứng Yên': [load_img(f'dungyen{i}.png') for i in range(1, 9)],
            'Chạy': load_chay_animation(),
            'Bắn': load_ban_animation(),
            'Trúng Đạn': load_trungdan_animation(),
            'Chết': [load_img(f'chet{i}.png') for i in range(1, 13)],
            'Nhảy': load_nhay_animation()
        }

        # ===== Trạng thái khởi tạo =====
        self.state = 'Đứng Yên'
        self.frame_index = 0
        self.huong_index = 0
        self.image = self.animations[self.state][self.huong_index]
        self.rect = self.image.get_rect(center=vi_tri)

        # ===== Nhóm sprite =====
        self.all_sprites = nhom_tat_ca
        self.bullets_group = nhom_dan

        # ===== Hướng nhìn =====
        self.huong_phai = True

        # ===== Chỉ số nhân vật =====
        self.max_hp = PLAYER_MAX_HP
        # Thiết lập máu gốc và hiện tại theo tham số truyền vào (nếu có)
        self.hp_goc = hp_goc if hp_goc is not None else self.max_hp
        self.hp = min(self.max_hp, self.hp_goc)
        self.magazine = PLAYER_MAGAZINE
        self.magazine_size = PLAYER_MAGAZINE
        self.reserve = PLAYER_RESERVE_MAX
        self.reserve_max = PLAYER_RESERVE_MAX
        self.reloading = False
        self.reload_time = RELOAD_TIME
        self._reload_timer = 0.0

        # ===== Di chuyển =====
        self.speed = PLAYER_SPEED
        self.jump_speed = PLAYER_SPEED * 2.0
        self.jump_distance = 150  # Quãng đường nhảy ngang
        self.jump_height = 80     # Độ cao nhảy (pixel)
        # Thời lượng nhảy dựa trên quãng đường và tốc độ (dùng để tính tiến độ theo thời gian)
        self.jump_duration = max(0.1, self.jump_distance / max(1.0, self.jump_speed))
        self.jump_time = 0.0
        
        # ===== Điều khiển animation =====
        self.anim_speeds = {
            'Đứng Yên': 0.08,
            'Chạy': 0.12,
            'Bắn': 0.9,
            'Chết': 0.10,
            'Trúng Đạn': 0.3,
            'Thay Đạn': 0.07,
            'Nhảy': 0.9
        }
        
        # ===== Trạng thái chết =====
        self.death_animation_finished = False

        # ===== Trạng thái nhảy =====
        self.is_jumping = False
        self.jump_start_pos = pygame.Vector2(0, 0)  # Vị trí bắt đầu nhảy
        self.jump_direction = pygame.Vector2(0, 0)  # Hướng nhảy
        self.jump_travelled = 0.0                   # Quãng đường đã đi
        self.jump_cooldown = 2.0  # hồi chiêu nhảy 2 giây
        self.last_jump_time = -999.0

        self.shoot_cooldown = 0.5
        self.last_shot_time = -999
        self.time_elapsed = 0.0

        # ===== Khiên =====
        self.shield_active = False
        self.shield_end_time = 0

        # ===== Camera offset (world -> screen) =====
        self.camera_offset = (0, 0)

        # ===== Bonus sát thương (mặc định 0 để an toàn) =====
        self.damage_bonus = 0

    

    # ===== Tính hướng từ vector =====
    def tinh_huong_tu_vector(self, vec):
        if vec.length() == 0:
            return self.huong_index
        import math
        angle = math.atan2(vec.y, vec.x) * 180 / math.pi
        if angle < 0:
            angle += 360
        if 337.5 <= angle or angle < 22.5:
            return 2
        elif 22.5 <= angle < 67.5:
            return 3
        elif 67.5 <= angle < 112.5:
            return 0
        elif 112.5 <= angle < 157.5:
            return 5
        elif 157.5 <= angle < 202.5:
            return 6
        elif 202.5 <= angle < 247.5:
            return 7
        elif 247.5 <= angle < 292.5:
            return 4
        else:
            return 1

    # ===== Tính hướng từ phím =====
    def tinh_huong_tu_phim(self, van_toc):
        if van_toc.length() == 0:
            return self.huong_index
        x, y = van_toc.x, van_toc.y
        if x == 0 and y == -1:
            return 4
        elif x == 1 and y == -1:
            return 1
        elif x == 1 and y == 0:
            return 2
        elif x == 1 and y == 1:
            return 3
        elif x == 0 and y == 1:
            return 0
        elif x == -1 and y == 1:
            return 5
        elif x == -1 and y == 0:
            return 6
        elif x == -1 and y == -1:
            return 7
        return self.huong_index

    # ===== Chuyển đổi huong_index sang hướng trúng đạn =====
    def lay_huong_trungdan(self):
        if self.huong_index in [0, 1, 7]:
            return 'thang'
        elif self.huong_index in [2, 3]:
            return 'phai'
        elif self.huong_index == 4:
            return 'xuong'
        else:
            return 'trai'

    # ===== Cập nhật animation =====
    def update_animation(self, dt=1/60):
        speed = self.anim_speeds.get(self.state, 0.1)
        if self.state in ['Bắn', 'Trúng Đạn']:
            speed *= 0.6

        # Đứng Yên
        if self.state == 'Đứng Yên':
            frames = self.animations[self.state]
            img = frames[self.huong_index]
        # Chạy, Bắn, Nhảy
        elif self.state in ['Chạy', 'Bắn', 'Nhảy']:
            self.frame_index += speed * dt * 60
            frames = self.animations[self.state][self.huong_index]
            if self.frame_index >= len(frames):
                if self.state == 'Bắn':
                    self.state = 'Đứng Yên'
                    self.frame_index = 0
                elif self.state == 'Nhảy':
                    # Animation nhảy lặp lại cho đến khi kết thúc nhảy
                    self.frame_index = 0
                else:
                    self.frame_index = 0
            img = frames[int(self.frame_index)]
        # Trúng Đạn
        elif self.state == 'Trúng Đạn':
            self.frame_index += speed * dt * 60
            huong = self.lay_huong_trungdan()
            frames = self.animations['Trúng Đạn'][huong]
            if self.frame_index >= len(frames):
                if self.hp > 0:
                    self.state = 'Đứng Yên'
                    self.frame_index = 0
            img = frames[int(self.frame_index)]
        # Chết
        elif self.state == 'Chết':
            self.frame_index += speed * dt * 60
            frames = self.animations[self.state]
            if self.frame_index >= len(frames):
                self.frame_index = len(frames) - 1
                self.death_animation_finished = True
            img = frames[int(self.frame_index)]
        else:
            # Các trạng thái khác
            self.frame_index += speed * dt * 60
            frames = self.animations[self.state]
            if self.frame_index >= len(frames):
                self.frame_index = 0
            img = frames[int(self.frame_index)]
            if not self.huong_phai and self.state not in ['Đứng Yên', 'Chạy', 'Bắn', 'Trúng Đạn', 'Nhảy']:
                img = pygame.transform.flip(img, True, False)

        pos = self.rect.center
        self.image = img
        self.rect = self.image.get_rect(center=pos)

    # ===== Cập nhật di chuyển =====
    def cap_nhat(self, dt, phim, vat_cans=None):
        self.update_animation(dt)
        self.time_elapsed += dt

        if self.state == 'Chết':
            return

        obstacles = vat_cans if vat_cans is not None else ()

        # XỬ LÝ NHẢY với chuyển động parabol
        if self.is_jumping:
            import math
            # Tiến độ nhảy dựa theo thời gian để tránh kẹt khi va chạm
            self.jump_time += dt
            move_amount = self.jump_speed * dt
            self.jump_travelled += move_amount  # quãng đường dự kiến (không phụ thuộc va chạm)

            # Di chuyển X theo hướng nhảy, có kiểm tra va chạm
            delta = self.jump_direction * move_amount
            self._move_axis(delta.x, obstacles, axis="x")

            # Tính độ cao theo parabol theo tiến độ thời gian
            progress = min(1.0, self.jump_time / self.jump_duration)
            height_offset = -4 * self.jump_height * progress * (progress - 1)
            target_y = self.jump_start_pos.y - height_offset
            dy = target_y - self.rect.centery
            self._move_axis(dy, obstacles, axis="y")

            # Kết thúc nhảy khi đạt 100% tiến độ hoặc quá thời lượng an toàn
            if progress >= 1.0 or self.jump_time >= self.jump_duration * 1.2:
                self.is_jumping = False
                self.jump_travelled = 0.0
                self.jump_time = 0.0
                self.state = 'Đứng Yên'
                self.frame_index = 0
            
            playable_rect = pygame.Rect(
                MAP_PLAYABLE_LEFT,
                MAP_PLAYABLE_TOP,
                MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
                MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
            )
            self.rect.clamp_ip(playable_rect)
            return

        # Di chuyển bình thường
        van_toc = pygame.Vector2(0, 0)
        if phim[pygame.K_w] or phim[pygame.K_UP]:
            van_toc.y = -1
        if phim[pygame.K_s] or phim[pygame.K_DOWN]:
            van_toc.y = 1
        if phim[pygame.K_a] or phim[pygame.K_LEFT]:
            van_toc.x = -1
            self.huong_phai = False
        if phim[pygame.K_d] or phim[pygame.K_RIGHT]:
            van_toc.x = 1
            self.huong_phai = True

        # Cập nhật hướng dựa trên vector di chuyển
        if van_toc.length() > 0:
            self.huong_index = self.tinh_huong_tu_phim(van_toc)

        # Cho phép di chuyển
        if van_toc.length() > 0:
            van_toc = van_toc.normalize()
            if self.state != 'Chết' and self.state != 'Trúng Đạn' and self.state != 'Bắn':
                # Chỉ chuyển sang Chạy nếu không đang bắn
                self.state = 'Chạy'
        else:
            if self.state not in ['Bắn', 'Trúng Đạn', 'Chết']:
                self.state = 'Đứng Yên'

        dx = van_toc.x * self.speed * dt
        dy = van_toc.y * self.speed * dt
        self._move_axis(dx, obstacles, axis="x")
        self._move_axis(dy, obstacles, axis="y")
        playable_rect = pygame.Rect(
            MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_TOP,
            MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
        )
        self.rect.clamp_ip(playable_rect)

        # NHẢY (Space hoặc Shift)
        now = self.time_elapsed
        if (phim[pygame.K_SPACE] or phim[pygame.K_LSHIFT]) and not self.is_jumping:
            if now - self.last_jump_time >= self.jump_cooldown:
                # Xác định hướng nhảy
                if van_toc.length() > 0:
                    dir_vec = van_toc.normalize()
                else:
                    dir_vec = pygame.Vector2(1 if self.huong_phai else -1, 0)
                self.bat_dau_nhay(dir_vec)
                self.last_jump_time = now

    def _move_axis(self, delta, obstacles, axis="x"):
        """Di chuyển theo một trục với kiểm tra va chạm vật cản.
        Kiểm tra phần chân (chạm vật cản từ tất cả các hướng).
        Dừng di chuyển mà không bị đẩy ngược."""
        if not delta:
            return False
        
        # Create collision zones (feet region - bottom, left edge, right edge)
        feet_height = max(1, self.rect.height // 3)
        
        # When moving on X-axis (left/right), check left/right collision zones
        if axis == "x":
            # Moving left (delta < 0) - check left edge
            if delta < 0:
                test_rect = pygame.Rect(
                    self.rect.x + delta,
                    self.rect.bottom - feet_height,
                    self.rect.width // 4,  # Left edge
                    feet_height
                )
            # Moving right (delta > 0) - check right edge
            else:
                test_rect = pygame.Rect(
                    self.rect.right + delta - self.rect.width // 4,
                    self.rect.bottom - feet_height,
                    self.rect.width // 4,  # Right edge
                    feet_height
                )
        # When moving on Y-axis, check bottom feet region
        else:
            test_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom - feet_height + delta,
                self.rect.width,
                feet_height
            )

        # Check if movement would collide with any obstacle
        collided = False
        for vat_can in obstacles:
            if test_rect.colliderect(vat_can.rect):
                collided = True
                break
        
        # Only move if no collision detected
        if not collided:
            if axis == "x":
                self.rect.x += delta
            else:
                self.rect.y += delta
        
        return collided

    # ===== Bắt đầu nhảy =====
    def bat_dau_nhay(self, huong: pygame.Vector2):
        if self.is_jumping or self.state == 'Chết':
            return
        if huong.length() == 0:
            huong = pygame.Vector2(1 if self.huong_phai else -1, 0)
        
        # Cập nhật hướng animation
        self.huong_index = self.tinh_huong_tu_phim(huong)
        
        self.jump_direction = huong.normalize()
        self.jump_start_pos = pygame.Vector2(self.rect.centerx, self.rect.centery)
        self.is_jumping = True
        self.jump_travelled = 0.0
        self.state = 'Nhảy'
        self.frame_index = 0

    # ===== Bắn =====
    def co_the_ban(self):
        time_since_last_shot = self.time_elapsed - self.last_shot_time
        return (not self.reloading
                and self.magazine > 0
                and not self.is_jumping
                and self.hp > 0
                and time_since_last_shot >= self.shoot_cooldown)

    def ban_vao_chuot(self, camera_offset=None):
        if not self.co_the_ban():
            return None
        mx, my = pygame.mouse.get_pos()
        # Dịch sang toạ độ thế giới theo camera offset (nếu có)
        ox, oy = (camera_offset if camera_offset is not None else self.camera_offset)
        world_mx, world_my = mx + (ox or 0), my + (oy or 0)
        dx, dy = world_mx - self.rect.centerx, world_my - self.rect.centery
        vec = pygame.Vector2(dx, dy)
        if vec.length() == 0:
            vec = pygame.Vector2(1, 0)

        # Cập nhật hướng nhìn theo vị trí chuột
        self.huong_index = self.tinh_huong_tu_vector(vec)

        vien_dan = Bullet(self.rect.center, vec, owner='player')
        self.all_sprites.add(vien_dan)
        self.bullets_group.add(vien_dan)
        self.magazine -= 1
        self.last_shot_time = self.time_elapsed
        self.state = 'Bắn'
        self.frame_index = 0
        
        # Phát âm thanh bắn súng
        try:
            sound_mgr = get_sound_manager()
            if sound_mgr:
                sound_mgr.play_tien_sung()
        except Exception:
            pass
        
        return vien_dan

    # ===== Nạp đạn =====
    def bat_dau_nap(self):
        if self.reloading or self.magazine >= self.magazine_size or self.reserve <= 0:
            return False
        can_them = self.magazine_size - self.magazine
        lay = min(can_them, self.reserve)
        self.magazine += lay
        self.reserve -= lay
        return True

    def _hoan_tat_nap(self):
        pass

    # ===== Trúng đạn =====
    def nhan_sat_thuong(self, so_luong=1):
        if self.hp <= 0:
            return
        self.hp -= so_luong
        if self.hp < 0:
            self.hp = 0
        self.frame_index = 0
        self.state = 'Trúng Đạn'
        if self.hp == 0:
            self.state = 'Chết'

    # ===== Khiên =====
    def kich_hoat_khien(self, thoi_gian_giay: float, now_ticks: int):
        self.shield_active = True
        self.shield_end_time = int(now_ticks + thoi_gian_giay * 1000)

    def cap_nhat_khien(self, now_ticks: int):
        if self.shield_active and now_ticks >= self.shield_end_time:
            self.shield_active = False

    # ===== Aliases =====
    update = cap_nhat
    can_shoot = co_the_ban
    shoot_at_mouse = ban_vao_chuot
    start_reload = bat_dau_nap
    _finish_reload = _hoan_tat_nap
    take_damage = nhan_sat_thuong


# ===== Hàm tiện ích cho người chơi =====

def tru_mau_nguoi_choi(nguoi_choi, sat_thuong):
    """Tru mau nguoi choi mot cach an toan
    
    Args:
        nguoi_choi: Instance cua NguoiChoi
        sat_thuong: So luong sat thuong
    """
    if not nguoi_choi or sat_thuong <= 0:
        return
    hp_truoc = getattr(nguoi_choi, "hp", 0)
    nhan_sat_thuong = getattr(nguoi_choi, "nhan_sat_thuong", None)
    if callable(nhan_sat_thuong):
        nhan_sat_thuong(sat_thuong)
    if getattr(nguoi_choi, "hp", hp_truoc) == hp_truoc:
        nguoi_choi.hp = max(0, hp_truoc - sat_thuong)


def cong_dan_nguoi_choi(nguoi_choi, amount=10):
    """Cong dan du tru cho nguoi choi
    
    Args:
        nguoi_choi: Instance cua NguoiChoi
        amount: So luong dan them vao
    """
    if hasattr(nguoi_choi, "reserve"):
        new_value = getattr(nguoi_choi, "reserve", 0) + amount
        reserve_max = getattr(nguoi_choi, "reserve_max", 9999)
        new_value = min(new_value, reserve_max)
        nguoi_choi.reserve = new_value
    # Khong goi cap_nhat_thong_so_dan de tranh thay doi magazine


def cap_nhat_ammo_bonus(nguoi_choi):
    """Cap nhat ammo bonus cho nguoi choi (neu co)
    
    Args:
        nguoi_choi: Instance cua NguoiChoi
    """
    bonus = getattr(nguoi_choi, "_ammo_bonus", None)
    if not bonus:
        return
    baseline = bonus.get("baseline", {})
    primary_attr = bonus.get("primary_attr")
    baseline_capacity = bonus.get("baseline_capacity")
    if not primary_attr or primary_attr not in baseline:
        return
    current = getattr(nguoi_choi, primary_attr, None)
    if current is None:
        return
    threshold = baseline_capacity if baseline_capacity is not None else baseline[primary_attr]
    if current > threshold:
        return
    default_baseline = getattr(nguoi_choi, "_ammo_baseline_default", {})
    for attr, _ in baseline.items():
        if hasattr(nguoi_choi, attr):
            restore = default_baseline.get(attr, baseline.get(attr))
            setattr(nguoi_choi, attr, restore)
    refresh = getattr(nguoi_choi, "cap_nhat_thong_so_dan", None)
    if callable(refresh):
        restore_val = default_baseline.get(primary_attr, baseline.get(primary_attr))
        if restore_val is not None:
            refresh(restore_val)
    nguoi_choi._ammo_bonus = None


Player = NguoiChoi