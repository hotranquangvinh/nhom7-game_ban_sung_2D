# dan.py - Đạn
import pygame
import math
from cau_hinh import (
    BULLET_SPEED, ENEMY_BULLET_SPEED, BAN_DO_RONG, BAN_DO_CAO,
    MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, MAP_PLAYABLE_RIGHT, MAP_PLAYABLE_BOTTOM
)

MAP_RECT = pygame.Rect(0, 0, BAN_DO_RONG, BAN_DO_CAO)
MAP_PLAYABLE_RECT = pygame.Rect(MAP_PLAYABLE_LEFT, MAP_PLAYABLE_TOP, 
                                 MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
                                 MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP)

class VienDan(pygame.sprite.Sprite):
    """
    Viên đạn có chủ sở hữu: 'player' hoặc 'enemy'
    direction: pygame.Vector2 đã chuẩn hóa
    speed: px/giây
    """
    def __init__(self, pos, direction, owner='player'):
        super().__init__()
        # normalize direction early so we can rotate the image to match it
        self.direction = direction.normalize() if direction.length() != 0 else pygame.Vector2(1, 0)
        # Kích thước khác nhau cho trực quan
        if owner == 'player':
            # Try to load bullet image from assets; fallback to simple colored surface
            try:
                img = pygame.image.load(r"assets/dan/dan1.png").convert_alpha()
                # scale to a reasonable size if the image is larger than expected
                target_size = (32, 16)
                if img.get_width() != target_size[0] or img.get_height() != target_size[1]:
                    img = pygame.transform.smoothscale(img, target_size)
                # rotate image so its nose/tip points along firing direction
                try:
                    angle = -math.degrees(math.atan2(self.direction.y, self.direction.x))
                    img = pygame.transform.rotate(img, angle)
                except Exception:
                    pass
                self.image = img
            except Exception:
                surf = pygame.Surface((32, 16), pygame.SRCALPHA)
                surf.fill((255, 230, 0))
                try:
                    angle = -math.degrees(math.atan2(self.direction.y, self.direction.x))
                    surf = pygame.transform.rotate(surf, angle)
                except Exception:
                    pass
                self.image = surf
            speed = BULLET_SPEED
        else:
            # Prefer a single-file art `assets/hinh_anh/dan_ke_thu.png` if present.
            try:
                import os, glob
                # Check if this is a boss bullet - use specific boss dan
                if owner == 'boss2':
                    single = os.path.join('assets', 'dan', 'dan_boss2.png')
                    target_size = (48, 24)  # Tăng từ 32x16 lên 48x24
                elif owner == 'boss3':
                    single = os.path.join('assets', 'dan', 'dan_boss3.png')
                    target_size = (48, 24)  # Tăng từ 32x16 lên 48x24
                else:
                    single = os.path.join('assets', 'hinh_anh', 'dan_ke_thu.png')
                    target_size = (24, 12)
                
                img = None
                if os.path.exists(single):
                    img = pygame.image.load(single)
                else:
                    # fallback: look for any images in the dan_ke_thu folder
                    folder = os.path.join('assets', 'hinh_anh', 'dan_ke_thu')
                    files = sorted(glob.glob(os.path.join(folder, '*.png')) + glob.glob(os.path.join(folder, '*.jpg')))
                    if files:
                        img = pygame.image.load(files[0])

                if img is not None:
                    try:
                        img = img.convert_alpha()
                    except Exception:
                        img = img.convert()
                    # scale to appropriate size
                    try:
                        img = pygame.transform.smoothscale(img, target_size)
                    except Exception:
                        img = pygame.transform.scale(img, target_size)
                    # rotate to match trajectory
                    try:
                        angle = -math.degrees(math.atan2(self.direction.y, self.direction.x))
                        img = pygame.transform.rotate(img, angle)
                    except Exception:
                        pass
                    self.image = img
                else:
                    raise FileNotFoundError()
            except Exception:
                surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                surf.fill((255, 80, 80))
                self.image = surf
            speed = ENEMY_BULLET_SPEED

        # set rect after any rotation so center stays at spawn position
        self.rect = self.image.get_rect(center=pos)
        self.owner = owner
        self.speed = speed

        # Alias tiếng Việt cho thuộc tính
        self.huong = self.direction
        self.chu_so_huu = self.owner
        self.toc_do = self.speed

    def cap_nhat(self, dt):
        # respect timestop freeze on bullets (freeze_end in ms)
        try:
            now_ms = pygame.time.get_ticks()
            if getattr(self, 'freeze_end', 0) > now_ms:
                return
        except Exception:
            pass

        self.rect.x += self.direction.x * self.speed * dt
        self.rect.y += self.direction.y * self.speed * dt

        # Kiểm tra boundary:
        # - Đạn người chơi: xóa khi ra ngoài toàn bộ map
        # - Đạn kẻ thú: xóa khi ra ngoài vùng chơi (MAP_PLAYABLE)
        if self.owner == 'player':
            if not MAP_RECT.colliderect(self.rect):
                self.kill()
        else:
            # Đạn kẻ thù không được vượt qua vùng chơi
            if not MAP_PLAYABLE_RECT.colliderect(self.rect):
                self.kill()

    # Alias tiếng Anh để tương thích với pygame.Group.update
    update = cap_nhat

# Alias tên lớp để tương thích với import cũ
Bullet = VienDan
