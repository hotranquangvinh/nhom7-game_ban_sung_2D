# ui.py
import os
import sys
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
    raise SystemExit("Thiếu pygame. Hãy chạy 'pip install pygame' trong môi trường ảo rồi thử lại.")

# Try to load health bar sprite images from assets/ui
# 5 sprites: mau1 (full HP/100%) to mau5 (empty HP/0%) - will switch based on current HP
HEALTH_BAR_SPRITES = []  # List of 5 sprites that change based on HP
AMMO_ICON = None  # Icon for ammo display
_images_loaded = False  # Track if we've loaded images yet

def _load_health_images():
    """Load 5 health bar sprites (mau1 = full HP/100%, mau5 = empty HP/0%) and ammo icon."""
    global HEALTH_BAR_SPRITES, AMMO_ICON, _images_loaded
    
    if _images_loaded:
        return  # Already loaded
    
    folder = os.path.join('assets', 'ui')
    if not os.path.isdir(folder):
        print(f"[UI] Thư mục {folder} không tồn tại!")
        _images_loaded = True
        return

    # Load mau1..mau5 as individual sprites and scale them down
    SCALE_HEIGHT = 50  # Chiều cao mới cho thanh máu (to hơn một tí)
    sprites = []
    for idx in range(1, 6):
        img = None
        # Try without space first
        name = f'mau{idx}.png'
        p = os.path.join(folder, name)
        if os.path.exists(p):
            try:
                img = pygame.image.load(p).convert_alpha()
                # Scale down maintaining aspect ratio
                original_w, original_h = img.get_size()
                scale_factor = SCALE_HEIGHT / original_h
                new_w = int(original_w * scale_factor)
                img = pygame.transform.smoothscale(img, (new_w, SCALE_HEIGHT))
                print(f"[UI] Đã load {name} - kích thước gốc: ({original_w}, {original_h}) -> scaled: {img.get_size()}")
            except Exception as e:
                print(f"[UI] Lỗi load {name}: {e}")
                img = None
        
        # Try with space (mau 4.png, mau 5.png)
        if img is None:
            name_space = f'mau {idx}.png'
            p_space = os.path.join(folder, name_space)
            if os.path.exists(p_space):
                try:
                    img = pygame.image.load(p_space).convert_alpha()
                    # Scale down maintaining aspect ratio
                    original_w, original_h = img.get_size()
                    scale_factor = SCALE_HEIGHT / original_h
                    new_w = int(original_w * scale_factor)
                    img = pygame.transform.smoothscale(img, (new_w, SCALE_HEIGHT))
                    print(f"[UI] Đã load {name_space} - kích thước gốc: ({original_w}, {original_h}) -> scaled: {img.get_size()}")
                except Exception as e:
                    print(f"[UI] Lỗi load {name_space}: {e}")
                    img = None
        
        if img is None:
            print(f"[UI] Không tìm thấy mau{idx}.png hoặc mau {idx}.png")
        
        sprites.append(img)
    
    # Store as list - index 0=mau1 (full HP), index 4=mau5 (empty HP)
    HEALTH_BAR_SPRITES = sprites
    
    valid_count = sum(1 for s in sprites if s is not None)
    if valid_count == 5:
        print(f"[UI] Đã load 5 sprite máu thành công (mau1=đầy 100%, mau5=rỗng 0%)")
    else:
        print(f"[UI] Chỉ load được {valid_count}/5 sprite máu")
    
    # Load ammo icon
    ammo_icon_path = os.path.join(folder, 'hinh_dan.png')
    if os.path.exists(ammo_icon_path):
        try:
            AMMO_ICON = pygame.image.load(ammo_icon_path).convert_alpha()
            # Scale to appropriate size (height ~40px - to hơn)
            original_w, original_h = AMMO_ICON.get_size()
            icon_height = 40
            scale_factor = icon_height / original_h
            new_w = int(original_w * scale_factor)
            AMMO_ICON = pygame.transform.smoothscale(AMMO_ICON, (new_w, icon_height))
            print(f"[UI] Đã load hinh_dan.png - kích thước: {AMMO_ICON.get_size()}")
        except Exception as e:
            print(f"[UI] Lỗi load hinh_dan.png: {e}")
            AMMO_ICON = None
    else:
        print(f"[UI] Không tìm thấy {ammo_icon_path}")
    
    _images_loaded = True

def ve_ui(man_hinh, nguoi_choi, phong_chu):
    # Load images on first call (after pygame.display is initialized)
    _load_health_images()
    
    # Mau: chon sprite dua tren HP hien tai (mau1=100%, mau2=80%, ..., mau5=0%)
    x_pos = 10
    y_pos = 10
    
    if len(HEALTH_BAR_SPRITES) == 5 and all(s is not None for s in HEALTH_BAR_SPRITES):
        # Calculate HP percentage
        hp_percent = (nguoi_choi.hp / nguoi_choi.hp_goc * 100) if nguoi_choi.hp_goc > 0 else 0
        
        # Select sprite index based on HP (REVERSED: mau1=full, mau5=empty)
        if hp_percent > 80:
            sprite_idx = 0  # mau1.png (81-100% HP - day mau)
        elif hp_percent > 60:
            sprite_idx = 1  # mau2.png (61-80% HP)
        elif hp_percent > 40:
            sprite_idx = 2  # mau3.png (41-60% HP)
        elif hp_percent > 20:
            sprite_idx = 3  # mau4.png (21-40% HP)
        else:
            sprite_idx = 4  # mau5.png (0-20% HP - sap chet)
        
        # Draw the selected sprite
        man_hinh.blit(HEALTH_BAR_SPRITES[sprite_idx], (x_pos, y_pos))

    # Dan: hien thi icon + so dan
    ammo_y = 64  # Vi tri Y cho phan dan (duoi thanh mau)
    
    if AMMO_ICON is not None:
        # Draw ammo icon
        man_hinh.blit(AMMO_ICON, (10, ammo_y))
        
        # Draw ammo text next to icon
        icon_width = AMMO_ICON.get_width()
        chu_dan = f"{nguoi_choi.magazine}/{nguoi_choi.magazine_size}  |  Du tru: {nguoi_choi.reserve}"
        be_mat_chu = phong_chu.render(chu_dan, True, (255, 255, 255))
        man_hinh.blit(be_mat_chu, (10 + icon_width + 8, ammo_y + 2))
    else:
        # Fallback to text-only if icon not loaded
        chu_dan = f"Bang: {nguoi_choi.magazine}/{nguoi_choi.magazine_size}  |  Du tru: {nguoi_choi.reserve}"
        be_mat_chu = phong_chu.render(chu_dan, True, (255, 255, 255))
        man_hinh.blit(be_mat_chu, (10, ammo_y))

    if nguoi_choi.reloading:
        t = phong_chu.render("Dang nap...", True, (255, 200, 0))
        man_hinh.blit(t, (10, ammo_y + 30))

# Alias tieng Anh de tuong thich
draw_ui = ve_ui
