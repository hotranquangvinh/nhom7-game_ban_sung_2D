# main.py
import os
import sys
import subprocess
import random
import site
EXTRA_SITE_PACKAGES = [
    site.getusersitepackages(),
    os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        r"Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages",
    ),
    os.path.join(os.path.dirname(sys.executable), "Lib", "site-packages"),
    os.path.join(os.path.dirname(sys.executable), "..", "Lib", "site-packages"),
]
for path in EXTRA_SITE_PACKAGES:
    if path and os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
try:
    import pygame
except ModuleNotFoundError:
    print("Thieu thu vien pygame. Vui long chay 'pip install pygame' trong moi truong ao roi thu lai.")
    sys.exit(1)

from cau_hinh import (
    RONG,
    CAO,
    SO_KHUNG_HINH,
    KHOANG_SINH_KE_THU,
    HINH_MEDKIT,
    HINH_SHIELD,
    HINH_DAN,
    HINH_TIMESTOP,
    BAN_DO_RONG,
    BAN_DO_CAO,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
    SO_VAT_CAN,
    VAT_CAN_THU_MUC,
    VAT_CAN_KHOANG_CACH,
    VAT_CAN_SCALE,
)
from nguoi_choi import NguoiChoi, tru_mau_nguoi_choi, cong_dan_nguoi_choi, cap_nhat_ammo_bonus
from ke_thu import Enemy
from ke_thu_2 import MeleeEnemy
from ke_thu_3 import JumperEnemy
from boss import Boss
from ui import ve_ui
from menu_game import MenuTroChoi
from map import GameMap, random_position_in_playable_area, is_position_valid, choose_spawn_position, tao_camera_rect, ve_nhom
from vatpham import Medkit, Shield, DanItem, TimeStop, DamageBoost, xoa_vat_pham_qua_han
from vatcan import VatCan, tai_hinh_vat_can, khoi_tao_vat_can
from dot import WaveManager
from tinhdiem import TinhDiem

ENEMY_SPAWN_INTERVAL = KHOANG_SINH_KE_THU * 2.0
# Periodic spawn intervals (seconds)
SPAWN_INTERVAL_NORMAL = 2.0
SPAWN_INTERVAL_MELEE = 3.0
SPAWN_INTERVAL_JUMPER = 5.0

# Periodic spawn timers (accumulators)
spawn_timer_normal = 0.0
spawn_timer_melee = 0.0
spawn_timer_jumper = 0.0
VAT_CAN_IMAGES: list[pygame.Surface] = []

# Hệ thống tính điểm
tinh_diem = TinhDiem()


# Set the project directory dynamically
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)  # Change the working directory to the project directory

FALLBACK_PYTHON = os.path.join(PROJECT_DIR, ".venv", "Scripts", "python.exe")

def _chon_python_hop_le():
    for candidate in (sys.executable, FALLBACK_PYTHON):
        if candidate and os.path.exists(candidate):
            return candidate
    return sys.executable

PYTHON_INTERPRETER = _chon_python_hop_le()
os.environ["PYTHON_EXECUTABLE"] = PYTHON_INTERPRETER

# Patch subprocess to use the current Python interpreter dynamically
_orig_popen = subprocess.Popen
_orig_run = subprocess.run

def _needs_python_repair(token):
    if isinstance(token, bytes):
        token = token.decode(sys.getfilesystemencoding(), errors="ignore")
    if not isinstance(token, str) or not token.strip():
        return False
    candidate = token.strip().strip('"').strip("'")
    return candidate.lower().endswith("python.exe") and not os.path.exists(candidate)

def _repair_python_command(command):
    if isinstance(command, bytes):
        repaired = _repair_python_command(command.decode(sys.getfilesystemencoding(), errors="ignore"))
        return repaired.encode(sys.getfilesystemencoding()) if isinstance(repaired, str) else command
    if isinstance(command, (list, tuple)):
        if command and _needs_python_repair(command[0]):
            fixed = list(command)
            fixed[0] = PYTHON_INTERPRETER
            return fixed
        return command
    if isinstance(command, str):
        parts = command.split()
        if parts and _needs_python_repair(parts[0]):
            head = parts[0]
            quoted = head and head[0] in "\"'"
            replacement = (
                f'"{PYTHON_INTERPRETER}"' if quoted or " " in PYTHON_INTERPRETER else PYTHON_INTERPRETER
            )
            return command.replace(head, replacement, 1)
    return command

def _patched_popen(command, *args, **kwargs):
    return _orig_popen(_repair_python_command(command), *args, **kwargs)

def _patched_run(command, *args, **kwargs):
    return _orig_run(_repair_python_command(command), *args, **kwargs)

subprocess.Popen = _patched_popen
subprocess.run = _patched_run

# Ensure all resource paths are relative to the project directory
HINH_SHIELD = os.path.join(PROJECT_DIR, HINH_SHIELD)
HINH_DAN = os.path.join(PROJECT_DIR, HINH_DAN)
HINH_TIMESTOP = os.path.join(PROJECT_DIR, HINH_TIMESTOP)
HINH_MEDKIT = os.path.join(PROJECT_DIR, HINH_MEDKIT)
HINH_DAN_SATTHUONG = os.path.join(PROJECT_DIR, 'assets', 'hinh_anh', 'dan_satthuong.png')

# Bubble shield overlay image (drawn around player while shield active)
BUBBLE_SHIELD_PATH = os.path.join(PROJECT_DIR, 'assets', 'hinh_anh', 'bubble_shield.png')

MEDKIT_ROTATION_SPEED = getattr(Medkit, "ROTATION_SPEED", 180.0)
SHIELD_ROTATION_SPEED = getattr(Shield, "ROTATION_SPEED", 360.0)

pygame.init()
man_hinh = pygame.display.set_mode((RONG, CAO))
pygame.display.set_caption("Game Ban Sung 2D")

# Khởi tạo mixer NGAY SAU KHI tạo display surface
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    print("✓ Mixer initialized successfully")
except Exception as mixer_err:
    print(f"✗ Mixer init error: {mixer_err}")

# Import audio manager SAU khi mixer đã init
from amthanh import quan_ly_am_thanh

dong_ho = pygame.time.Clock()
phong_chu = pygame.font.SysFont(None, 28)
ban_do = GameMap(PROJECT_DIR)
VAT_CAN_IMAGES = tai_hinh_vat_can(os.path.join(PROJECT_DIR, VAT_CAN_THU_MUC), scale=VAT_CAN_SCALE)

# Menu / trạng thái
menu_tro_choi = MenuTroChoi(man_hinh, phong_chu)  # Đảm bảo truyền cả 'man_hinh' và 'phong_chu'

# Nhóm sprite
tat_ca_sprite = pygame.sprite.Group()
nhom_ke_thu = pygame.sprite.Group()
nhom_dan = pygame.sprite.Group()
vat_cans = pygame.sprite.Group()
# Wave manager (initialized when a new round starts)
wave_manager = None
# Khởi tạo người chơi và bộ đếm sinh kẻ
nguoi_choi = None
dem_sinh_ke = 0.0

# Nhóm Medkit
medkits = pygame.sprite.Group()
MEDKIT_SPAWN_EVENT = pygame.USEREVENT + 10
pygame.time.set_timer(MEDKIT_SPAWN_EVENT, 10000)  # 10 giây spawn nhanh hơn
player_health = 6  # máu gốc khi bắt đầu game

# Nhóm khiên
shields = pygame.sprite.Group()
SHIELD_SPAWN_EVENT = pygame.USEREVENT + 11
pygame.time.set_timer(SHIELD_SPAWN_EVENT, 15000)  # 15 giây spawn nhanh hơn

# Nhóm ngừng thời gian
timestops = pygame.sprite.Group()
TIMESTOP_SPAWN_EVENT = pygame.USEREVENT + 12
pygame.time.set_timer(TIMESTOP_SPAWN_EVENT, 20000)  # 20 giây spawn nhanh hơn

# Nhóm đạn đặc biệt
dan_items = pygame.sprite.Group()
DAN_ITEM_SPAWN_EVENT = pygame.USEREVENT + 13
pygame.time.set_timer(DAN_ITEM_SPAWN_EVENT, 7000)   # 7 giây spawn nhanh hơn

# Nhóm đạn sát thương (tăng sát thương tạm thời khi nhặt)
damage_items = pygame.sprite.Group()
DAMAGE_ITEM_SPAWN_EVENT = pygame.USEREVENT + 14
pygame.time.set_timer(DAMAGE_ITEM_SPAWN_EVENT, 12000)  # 12 giây spawn

# Biến debug message
debug_message_text = ""
debug_message_until = 0


# Tải và scale hình ảnh cho Hộp đạn
try:
    HINH_DAN_IMAGE = pygame.transform.scale(pygame.image.load(HINH_DAN), (32, 32))
except FileNotFoundError:
    print(f"Loi: Khong tim thay file '{HINH_DAN}'.")
    sys.exit(1)

# Load bubble shield image (optional). Keep original source and scale per-frame to fit player.
try:
    BUBBLE_SHIELD_SRC = pygame.image.load(BUBBLE_SHIELD_PATH).convert_alpha()
except Exception:
    BUBBLE_SHIELD_SRC = None


def bat_dau_vong_moi():
    global tat_ca_sprite, nhom_ke_thu, nhom_dan, vat_cans, nguoi_choi, dem_sinh_ke, player_health, medkits, shields, dan_items, wave_manager
    # Reset điểm khi bắt đầu game mới
    tinh_diem.reset()
    # Reset victory flag
    menu_tro_choi.victory_triggered = False
    menu_tro_choi.is_victory = False
    tat_ca_sprite.empty(); nhom_ke_thu.empty(); nhom_dan.empty(); vat_cans.empty()
    # Spawn nguoi choi - o duoi trong che do kho, o giua trong che do binh thuong
    from che_do import difficulty
    if difficulty.is_hard_mode():
        # Che do kho: o duoi man hinh
        vi_tri_bat_dau = (
            (MAP_PLAYABLE_LEFT + MAP_PLAYABLE_RIGHT) // 2,
            MAP_PLAYABLE_BOTTOM - 100  # O duoi
        )
        # Che do kho: phat nhac danh_boss tu dau
        quan_ly_am_thanh.stop_music()
        quan_ly_am_thanh.play_nhac_boss()
    else:
        # Che do binh thuong: o giua
        vi_tri_bat_dau = (
            (MAP_PLAYABLE_LEFT + MAP_PLAYABLE_RIGHT) // 2,
            (MAP_PLAYABLE_TOP + MAP_PLAYABLE_BOTTOM) // 2
        )
        # Che do binh thuong: phat nhac nen binh thuong
        quan_ly_am_thanh.stop_music()
        quan_ly_am_thanh.play_nhac_nen()
    
    nguoi_choi = NguoiChoi(vi_tri_bat_dau, tat_ca_sprite, nhom_dan, hp_goc=player_health)
    nguoi_choi.hp = player_health  # Đảm bảo máu hiện tại = máu gốc khi bắt đầu game
    max_cam_x = max(0, BAN_DO_RONG - RONG)
    max_cam_y = max(0, BAN_DO_CAO - CAO)
    cam_x = max(0, min(vi_tri_bat_dau[0] - RONG // 2, max_cam_x))
    cam_y = max(0, min(vi_tri_bat_dau[1] - CAO // 2, max_cam_y))
    nguoi_choi.camera_offset = (cam_x, cam_y)
    tat_ca_sprite.add(nguoi_choi)
    medkits.empty()
    shields.empty()
    dan_items.empty()
    khoi_tao_vat_can(vat_cans, VAT_CAN_IMAGES, SO_VAT_CAN, [nguoi_choi.rect.inflate(VAT_CAN_KHOANG_CACH * 2, VAT_CAN_KHOANG_CACH * 2)])

    # Khởi tạo WaveManager và bắt đầu đợt 1
    wave_manager = WaveManager(nguoi_choi, tat_ca_sprite, nhom_dan, None, enemies_group=nhom_ke_thu)
    wave_manager.start_wave(0)
    dem_sinh_ke = 0.0
    # reset periodic spawn timers
    global spawn_timer_normal, spawn_timer_melee, spawn_timer_jumper
    spawn_timer_normal = 0.0
    spawn_timer_melee = 0.0
    spawn_timer_jumper = 0.0

# Khởi đầu ở menu
menu_tro_choi.state = "menu"
# Không phát nhạc ở menu, chỉ phát khi chọn chế độ
dang_chay = True
while dang_chay:
    dt = dong_ho.tick(SO_KHUNG_HINH) / 1000.0
    now_ticks = pygame.time.get_ticks()

    for su_kien in pygame.event.get():
        if su_kien.type == pygame.QUIT:
            # Khong cho thoat neu dang o man hinh nhap ten
            if menu_tro_choi.state != "input_name":
                dang_chay = False
        if su_kien.type == pygame.KEYDOWN and su_kien.key == pygame.K_ESCAPE:
            # If currently playing, toggle pause overlay
            # If at input_name, do NOT allow exit (must enter name first)
            try:
                if menu_tro_choi.state == "playing":
                    menu_tro_choi.toggle_pause()
                elif menu_tro_choi.state == "input_name":
                    pass  # Khong cho thoat, bat buoc nhap ten
                else:
                    dang_chay = False
            except Exception:
                dang_chay = False

        # Chuột
        if su_kien.type == pygame.MOUSEBUTTONDOWN:
            if menu_tro_choi.state in ("menu", "difficulty_select", "gameover", "input_name", "leaderboard"):
                menu_tro_choi.xu_ly_click(su_kien.pos)
                if menu_tro_choi.state == "playing":
                    bat_dau_vong_moi()
                # If exit icon is present on the menu and clicked, quit immediately
                try:
                    if menu_tro_choi.state == 'menu' and getattr(menu_tro_choi, 'menu_exit_rect', None) and menu_tro_choi.menu_exit_rect.collidepoint(su_kien.pos):
                        dang_chay = False
                        break
                except Exception:
                    pass
            elif menu_tro_choi.state == "playing":
                # If paused, route clicks to pause menu buttons
                if getattr(menu_tro_choi, 'paused', False):
                    result = menu_tro_choi.handle_pause_click(su_kien.pos)
                    if result == 'exit':
                        # user chose to exit from the pause menu — quit the program
                        dang_chay = False
                        break
                else:
                    if su_kien.button == 1 and nguoi_choi:
                        offset = getattr(nguoi_choi, "camera_offset", (0, 0))
                        nguoi_choi.ban_vao_chuot(offset)
        
        # Xử lý input khi nhập tên
        if su_kien.type == pygame.KEYDOWN and menu_tro_choi.state == "input_name":
            menu_tro_choi.handle_key_input(su_kien)

        # Nạp đạn (ignore while paused)
        if su_kien.type == pygame.KEYDOWN and menu_tro_choi.state == "playing" and not getattr(menu_tro_choi, 'paused', False):
            if su_kien.key == pygame.K_r and nguoi_choi:
                nguoi_choi.bat_dau_nap()

        # Sinh Medkit (skip while paused)
        if su_kien.type == MEDKIT_SPAWN_EVENT and menu_tro_choi.state == "playing" and not getattr(menu_tro_choi, 'paused', False):
            x, y = choose_spawn_position(prob_center=0.35, center_radius=150, margin=50, obstacles=vat_cans)
            medkit = Medkit(x, y)
            medkit.spawn_time_ms = pygame.time.get_ticks()
            medkits.add(medkit)

        # Sinh Khien (animated frames) (skip while paused)
        if su_kien.type == SHIELD_SPAWN_EVENT and menu_tro_choi.state == "playing" and not getattr(menu_tro_choi, 'paused', False):
            x, y = choose_spawn_position(prob_center=0.35, center_radius=150, margin=50, obstacles=vat_cans)
            # Load all shield frames from assets/hinh_anh/khien/
            shield = Shield(
                x, y,
                frame_dir=os.path.join(PROJECT_DIR, 'assets', 'hinh_anh', 'khien'),
                size=(32, 32),
                animation_speed=0.1
            )
            shield.spawn_time_ms = pygame.time.get_ticks()
            shields.add(shield)

        # Sinh Hop dan (skip while paused)
        if su_kien.type == DAN_ITEM_SPAWN_EVENT and menu_tro_choi.state == "playing" and not getattr(menu_tro_choi, 'paused', False):
            x, y = choose_spawn_position(prob_center=0.35, center_radius=150, margin=50, obstacles=vat_cans)
            dan_item = DanItem(x, y)
            dan_item.image = HINH_DAN_IMAGE  # Gan hinh anh cho Hop dan
            dan_item.spawn_time_ms = pygame.time.get_ticks()
            dan_items.add(dan_item)

        # Sinh Dan sat thuong (tang sat thuong tam thoi khi nhat)
        if su_kien.type == DAMAGE_ITEM_SPAWN_EVENT and menu_tro_choi.state == "playing" and not getattr(menu_tro_choi, 'paused', False):
            x, y = choose_spawn_position(prob_center=0.35, center_radius=150, margin=50, obstacles=vat_cans)
            try:
                dmg = DamageBoost(x, y, image_path=HINH_DAN_SATTHUONG, size=(32, 32))
            except Exception:
                # fallback to simple DamageBoost without explicit image
                dmg = DamageBoost(x, y, size=(32, 32))
            dmg.spawn_time_ms = pygame.time.get_ticks()
            damage_items.add(dmg)

        # Sinh TimeStop (dong ho xoay) (skip while paused)
        if su_kien.type == TIMESTOP_SPAWN_EVENT and menu_tro_choi.state == "playing" and not getattr(menu_tro_choi, 'paused', False):
            x, y = choose_spawn_position(prob_center=0.35, center_radius=150, margin=50, obstacles=vat_cans)
            timestop = TimeStop(x, y)
            timestop.spawn_time_ms = pygame.time.get_ticks()
            timestops.add(timestop)

    if menu_tro_choi.state == "menu":
        menu_tro_choi.ve_menu()
    elif menu_tro_choi.state == "difficulty_select":
        menu_tro_choi.ve_chon_che_do()
    elif menu_tro_choi.state == "playing":
        # If paused, skip all updates but still draw the current frame and show pause UI
        if not getattr(menu_tro_choi, 'paused', False):
            # NOTE: Enemy spawning is now controlled by WaveManager (dot.py)
            # The old time-based spawn has been disabled to let waves determine spawn counts.

            # WaveManager now controls scheduled spawns per-wave.
            # (Old periodic spawn timers have been retained for backward compatibility but are unused.)

            # Cập nhật tất cả sprite (Enemy tự kiểm tra freeze_end)
            phim = pygame.key.get_pressed()
            for obj in list(tat_ca_sprite):
                if isinstance(obj, NguoiChoi):
                    obj.cap_nhat(dt, phim, vat_cans)
                    obj.cap_nhat_khien(now_ticks)  # Tắt khiên đúng thời điểm
                elif isinstance(obj, Enemy):
                    obj.update(dt, vat_cans)
                elif hasattr(obj, 'update'):
                    try:
                        obj.update(dt)
                    except TypeError:
                        obj.update()

            medkits.update(dt)
            shields.update(dt)         # animate shields
            timestops.update(dt)
            dan_items.update(dt)       # bounce animation for ammo boxes
            damage_items.update(dt)    # damage boost items
            xoa_vat_pham_qua_han(medkits, now_ticks)
            xoa_vat_pham_qua_han(shields, now_ticks)
            xoa_vat_pham_qua_han(dan_items, now_ticks)
            xoa_vat_pham_qua_han(damage_items, now_ticks)
            xoa_vat_pham_qua_han(timestops, now_ticks)

            # Va chạm: đạn người chơi -> kẻ thù, đạn kẻ thù -> người chơi
            for vien_dan in list(nhom_dan):
                if pygame.sprite.spritecollide(vien_dan, vat_cans, False):
                    vien_dan.kill()
                    continue
                if getattr(vien_dan, 'chu_so_huu', None) == 'player':
                    trung = pygame.sprite.spritecollide(vien_dan, nhom_ke_thu, False)
                    if trung:
                        vien_dan.kill()
                        co_so = getattr(vien_dan, "sat_thuong", 1)
                        cong = getattr(nguoi_choi, "damage_bonus", 0) if nguoi_choi else 0
                        sat_thuong = max(1, co_so + cong)
                        for ke_thu in trung:
                            hp_trc = getattr(ke_thu, 'hp', 0)
                            ke_thu.nhan_sat_thuong(sat_thuong)
                            hp_sau = getattr(ke_thu, 'hp', 0)
                            # Nếu HP giảm xuống 0 hoặc dưới, tính điểm
                            if hp_trc > 0 and hp_sau <= 0:
                                enemy_type = type(ke_thu).__name__
                                if enemy_type == 'Enemy':
                                    tinh_diem.cong_diem_tieu_diet_ke_thu('enemy_1')
                                elif enemy_type == 'MeleeEnemy':
                                    tinh_diem.cong_diem_tieu_diet_ke_thu('enemy_2')
                                elif enemy_type == 'JumperEnemy':
                                    tinh_diem.cong_diem_tieu_diet_ke_thu('enemy_3')
                                elif enemy_type == 'Boss':
                                    tinh_diem.cong_diem_tieu_diet_ke_thu('boss_1')
                                elif 'Boss2' in enemy_type:
                                    tinh_diem.cong_diem_tieu_diet_ke_thu('boss_2')
                                elif 'Boss3' in enemy_type:
                                    tinh_diem.cong_diem_tieu_diet_ke_thu('boss_3')
                                ke_thu.kill()
                else:
                    if not hasattr(vien_dan, 'spawn_time_ms'):
                        vien_dan.spawn_time_ms = now_ticks
                    if now_ticks - vien_dan.spawn_time_ms >= 10000:  # Tăng từ 5s lên 10s để đạn kẻ thù bay xa hơn
                        vien_dan.kill()
                        continue
                    if nguoi_choi and nguoi_choi.hp > 0 and vien_dan.rect.colliderect(nguoi_choi.rect):
                        vien_dan.kill()
                        if nguoi_choi.shield_active:
                            continue
                        # Skip damage if player is jumping (immune during jump)
                        if getattr(nguoi_choi, 'is_jumping', False):
                            continue
                        tinh_diem.trat_diem_bi_dan()
                        tru_mau_nguoi_choi(nguoi_choi, 1)
                        if nguoi_choi.hp <= 0:
                            nguoi_choi.state = 'Chết'
                            menu_tro_choi.current_score = tinh_diem.get_diem()
                            menu_tro_choi.is_victory = False  # Thua cuoc, khong chinh phuc
                            menu_tro_choi.input_active = False
                            # Không chuyển sang input_name ngay mà chờ animation chết xong

            # Va cham: ke thu cham nguoi choi (luon kiem tra va cham, ke ca khi dang ngung thoi gian)
            if nguoi_choi and nguoi_choi.hp > 0:
                # Neu shield active, khong gay damage tu touch
                if nguoi_choi.shield_active:
                    pass  # Shield miễn nhiễm tất cả va chạm
                else:
                    # Don't auto-kill collided enemies here; handle per-type so boss isn't removed by sprite.kill()
                    danh_sach = pygame.sprite.spritecollide(nguoi_choi, nhom_ke_thu, False)
                    if danh_sach:
                        # If player is jumping, immune to touch damage
                        if getattr(nguoi_choi, 'is_jumping', False):
                            pass
                        else:
                            # Per-enemy touch cooldown (ms)
                            touch_cooldown_ms = 500
                            # Player invulnerability after being knocked (ms) to avoid rapid multi-hits
                            player_invul_ms = getattr(nguoi_choi, 'invul_ms', 800)
                            invul_until = getattr(nguoi_choi, 'invulnerable_until', -1)
                            knocked_any = False

                            for enemy in danh_sach:
                                # Boss chi gay damage khi o trang thai "dash"
                                if getattr(enemy, 'is_boss', False) and getattr(enemy, 'state', None) != 'dash':
                                    continue
                                
                                try:
                                    last_touch = getattr(enemy, 'last_touch_ticks', -999999)
                                except Exception:
                                    last_touch = -999999

                                # only allow touch-damage if enemy cooldown expired and player not currently invulnerable
                                if now_ticks - last_touch >= touch_cooldown_ms and now_ticks >= invul_until:
                                    # apply single damage for this enemy-touch
                                    tru_mau_nguoi_choi(nguoi_choi, 1)
                                    try:
                                        enemy.last_touch_ticks = now_ticks
                                    except Exception:
                                        pass

                                    # knockback removed: player position is no longer changed on touch

                                    # set player's invulnerability window so subsequent touches don't hurt immediately
                                    try:
                                        nguoi_choi.invulnerable_until = now_ticks + player_invul_ms
                                    except Exception:
                                        pass
                                    knocked_any = True

                            # If player died from touch(s), trigger gameover
                            if nguoi_choi.hp <= 0:
                                nguoi_choi.state = 'Chết'
                                menu_tro_choi.current_score = tinh_diem.get_diem()
                                menu_tro_choi.is_victory = False  # Thua cuoc, khong chinh phuc
                                menu_tro_choi.input_active = False
                                # Khong chuyen sang input_name ngay ma cho animation chet xong

            # Kiểm tra va chạm và cập nhật khiên, máu, ngừng thời gian
            if nguoi_choi and nguoi_choi.hp > 0:
                # Clear temporary damage bonus if expired
                try:
                    endt = getattr(nguoi_choi, 'damage_bonus_end_time', None)
                    if endt is not None and now_ticks >= endt:
                        nguoi_choi.damage_bonus = 0
                        nguoi_choi.damage_bonus_end_time = None
                except Exception:
                    pass

                medkit_hits = pygame.sprite.spritecollide(nguoi_choi, medkits, dokill=True)
                for _ in medkit_hits:
                    if nguoi_choi.hp < nguoi_choi.hp_goc:
                        nguoi_choi.hp += 1
                    quan_ly_am_thanh.play_nhat_item()

                shield_hits = pygame.sprite.spritecollide(nguoi_choi, shields, dokill=True)
                for _ in shield_hits:
                    if not nguoi_choi.shield_active:
                        nguoi_choi.kich_hoat_khien(5, now_ticks)
                    quan_ly_am_thanh.play_nhat_item()

                dan_hits = pygame.sprite.spritecollide(nguoi_choi, dan_items, dokill=True)
                for _ in dan_hits:
                    cong_dan_nguoi_choi(nguoi_choi)
                    quan_ly_am_thanh.play_nhat_item()

                # Đạn sát thương: tăng sát thương tạm thời khi nhặt
                damage_hits = pygame.sprite.spritecollide(nguoi_choi, damage_items, dokill=True)
                for _ in damage_hits:
                    # Thiết lập bonus +1 sát thương trong 10 giây
                    try:
                        nguoi_choi.damage_bonus = getattr(nguoi_choi, 'damage_bonus', 0) + 1
                        nguoi_choi.damage_bonus_end_time = now_ticks + 10000
                        # show transient debug message
                        debug_message_text = f"Damage +1 cho 10s"
                        debug_message_until = now_ticks + 1500
                        quan_ly_am_thanh.play_nhat_item()
                    except Exception:
                        pass

                timestop_hits = pygame.sprite.spritecollide(nguoi_choi, timestops, dokill=True)
                for _ in timestop_hits:
                        quan_ly_am_thanh.play_nhat_item()
                        # Set freeze_end on enemies for 3 seconds.
                        # Prefer to freeze only the current wave's enemies (so it affects that encounter)
                        freeze_until = now_ticks + 3000
                        # choose target group: current wave's enemies if wave_manager exists, otherwise global nhom_ke_thu
                        try:
                            if 'wave_manager' in globals() and wave_manager is not None:
                                target_group = wave_manager.current_enemies
                            else:
                                target_group = nhom_ke_thu
                        except Exception:
                            target_group = nhom_ke_thu

                        try:
                            count = len(target_group)
                        except Exception:
                            # fallback
                            count = len(nhom_ke_thu)

                        print(f"[DEBUG] TimeStop picked at {now_ticks}, freezing {count} enemies until {freeze_until}")
                        for enemy in list(target_group):
                            try:
                                enemy.freeze_end = freeze_until
                            except Exception:
                                pass
                        # Also ensure every enemy instance in the global enemy group is frozen,
                        # including types defined in ke_thu, ke_thu_2, ke_thu_3 and boss.
                        try:
                            frozen_extra = 0
                            for enemy in list(nhom_ke_thu):
                                try:
                                    # only set for typical enemy classes (avoid player/items)
                                    if isinstance(enemy, (Enemy, MeleeEnemy, JumperEnemy, Boss)):
                                        enemy.freeze_end = freeze_until
                                        frozen_extra += 1
                                except Exception:
                                    # best-effort: try to set attribute anyway
                                    try:
                                        enemy.freeze_end = freeze_until
                                        frozen_extra += 1
                                    except Exception:
                                        pass
                        except Exception:
                            frozen_extra = 0
                        # freeze existing enemy bullets as well (owner != 'player')
                        try:
                            for bullet in list(nhom_dan):
                                if getattr(bullet, 'owner', getattr(bullet, 'chu_so_huu', None)) != 'player':
                                    try:
                                        bullet.freeze_end = freeze_until
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        # set on-screen debug message for 1.5s so it's visible without console
                        try:
                            debug_message_text = f"TimeStop: frozen {count} enemies"
                            debug_message_until = now_ticks + 1500
                        except Exception:
                            pass

        if nguoi_choi:
            camera_rect = tao_camera_rect(nguoi_choi.rect)
            nguoi_choi.camera_offset = camera_rect.topleft
        else:
            camera_rect = pygame.Rect(0, 0, RONG, CAO)
        offset = (-camera_rect.x, -camera_rect.y)

        # Cập nhật WaveManager (nếu có)
        try:
            if wave_manager is not None:
                wave_manager.update_with_dt(dt)
                # Kiem tra neu hoan thanh tat ca cac dot
                if wave_manager.all_waves_completed and not getattr(menu_tro_choi, 'victory_triggered', False):
                    menu_tro_choi.victory_triggered = True
                    menu_tro_choi.is_victory = True  # Co chinh phuc tat ca cac dot
                    # Tinh diem cuoi cung
                    menu_tro_choi.current_score = tinh_diem.get_diem()
                    # Phát âm thanh chiến thắng
                    quan_ly_am_thanh.play_chuc_mung_chien_thang()
                    # Chuyen sang input name de luu diem
                    menu_tro_choi.state = "input_name"
        except Exception:
            # avoid breaking game loop if wave manager has an issue
            pass

        # Kiểm tra animation chết xong của người chơi
        if nguoi_choi and nguoi_choi.hp <= 0:
            # Phát âm thanh thất bại khi chết (nếu chưa phát)
            if not getattr(quan_ly_am_thanh, 'am_thanh_that_bai_playing', False):
                quan_ly_am_thanh.play_am_thanh_that_bai()
            # Chuyển sang input_name khi animation chết xong
            if getattr(nguoi_choi, 'death_animation_finished', False):
                menu_tro_choi.input_active = True
                menu_tro_choi.state = "input_name"

        ban_do.draw(man_hinh, camera_rect)
        ve_nhom(vat_cans, man_hinh, offset)
        ve_nhom(medkits, man_hinh, offset)
        ve_nhom(shields, man_hinh, offset)
        ve_nhom(dan_items, man_hinh, offset)
        ve_nhom(damage_items, man_hinh, offset)
        ve_nhom(timestops, man_hinh, offset)
        ve_nhom(tat_ca_sprite, man_hinh, offset)
        for ke_thu in nhom_ke_thu:
            ke_thu.ve_thanh_mau(man_hinh, offset)

        # If player has shield active, draw bubble shield overlay around player (over the player sprites)
        try:
            if nguoi_choi and getattr(nguoi_choi, 'shield_active', False) and getattr(nguoi_choi, 'hp', 0) > 0 and BUBBLE_SHIELD_SRC:
                # Scale bubble so it fully contains the player plus padding
                p_w, p_h = nguoi_choi.rect.width, nguoi_choi.rect.height
                pad_w, pad_h = 50, 60  # horizontal and vertical padding around player inside bubble
                target_w = max(1, int(p_w + pad_w))
                target_h = max(1, int(p_h + pad_h))
                try:
                    bubble = pygame.transform.smoothscale(BUBBLE_SHIELD_SRC, (target_w, target_h))
                except Exception:
                    bubble = BUBBLE_SHIELD_SRC
                bx = nguoi_choi.rect.centerx + offset[0] - bubble.get_width() // 2
                # nudge bubble up slightly so the top rim clears the player's head
                by = nguoi_choi.rect.centery + offset[1] - bubble.get_height() // 2 - 6
                man_hinh.blit(bubble, (bx, by))
        except Exception:
            pass

        # Vẽ thông báo chuyển đợt (nếu có)
        if 'wave_manager' in globals() and wave_manager is not None:
            wave_manager.draw_transition_message(man_hinh, phong_chu)

        # draw transient debug message if set
        try:
            if debug_message_text and now_ticks < debug_message_until:
                msg_surf = phong_chu.render(debug_message_text, True, (255, 255, 0))
                msg_rect = msg_surf.get_rect(center=(RONG // 2, 40))
                pygame.draw.rect(man_hinh, (0, 0, 0), msg_rect.inflate(10, 8))
                man_hinh.blit(msg_surf, msg_rect.topleft)
        except Exception:
            pass

        if nguoi_choi:
            # If paused, show pause overlay after drawing the world/UI
            ve_ui(man_hinh, nguoi_choi, phong_chu)
            try:
                if getattr(menu_tro_choi, 'paused', False):
                    menu_tro_choi.ve_pause()
            except Exception:
                pass
            if nguoi_choi.hp > 0 and nguoi_choi.shield_active:
                thoi_gian_con_lai = max(0, (nguoi_choi.shield_end_time - now_ticks) // 1000)
                shield_text = phong_chu.render(f"Khien con: {thoi_gian_con_lai}s", True, (0, 191, 255))
                text_rect = shield_text.get_rect(topleft=(10, 90))
                pygame.draw.rect(man_hinh, (30, 30, 30), text_rect)
                man_hinh.blit(shield_text, text_rect.topleft)
    elif menu_tro_choi.state == "gameover":
        menu_tro_choi.ve_thua_cuoc()
    elif menu_tro_choi.state == "input_name":
        menu_tro_choi.ve_nhap_ten()
    elif menu_tro_choi.state == "leaderboard":
        menu_tro_choi.ve_leaderboard()

    pygame.display.flip()

pygame.quit()
sys.exit()
