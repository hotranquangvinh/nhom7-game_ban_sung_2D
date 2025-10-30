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
import glob


def xoa_vat_pham_qua_han(group, now_ticks, lifetime_ms=7000):
    """Xoa cac vat pham da spawn qua lau
    
    Args:
        group: Sprite group chua vat pham
        now_ticks: Thoi gian hien tai (pygame.time.get_ticks())
        lifetime_ms: Thoi gian ton tai toi da (milliseconds)
    """
    for sprite in list(group):
        bat_dau = getattr(sprite, "spawn_time_ms", None)
        if bat_dau is None:
            sprite.spawn_time_ms = now_ticks
            continue
        if now_ticks - bat_dau >= lifetime_ms:
            sprite.kill()


def _update_bounce(obj, dt):
    """Generic two-stage spawn bounce: first bounce higher, second smaller."""
    # initialize bounce params on first call
    if not getattr(obj, '_bounce_initialized', False):
        obj._bounce_initialized = True
        obj.gravity = getattr(obj, 'gravity', 1500.0)
        # initial upward impulse (px/s)
        obj.vy = getattr(obj, 'initial_jump', -420.0)
        # record ground level (rect.bottom at spawn)
        obj.ground_y = getattr(obj, 'ground_y', obj.rect.bottom)
        obj.bounces_done = 0
        obj.max_bounces = getattr(obj, 'max_bounces', 2)
        obj.bounce_dampings = getattr(obj, 'bounce_dampings', [0.6, 0.4])
        obj.landed = False

    if getattr(obj, 'landed', False):
        return

    # integrate velocity
    obj.vy += obj.gravity * dt
    # move by vy (use float accumulator to avoid losing precision)
    new_y = obj.rect.y + obj.vy * dt
    obj.rect.y = int(new_y)

    # hit ground
    if obj.rect.bottom >= obj.ground_y:
        obj.rect.bottom = obj.ground_y
        if obj.bounces_done < obj.max_bounces:
            # invert velocity and dampen for next bounce
            damping = obj.bounce_dampings[obj.bounces_done] if obj.bounces_done < len(obj.bounce_dampings) else 0.4
            obj.vy = -abs(obj.vy) * damping
            obj.bounces_done += 1
        else:
            obj.vy = 0
            obj.landed = True


class Medkit(pygame.sprite.Sprite):
    def __init__(self, x, y, frames=None, frame_paths=None, size=(32, 32)):
        super().__init__()
        default_paths = [os.path.join("assets", "hinh_anh", "mau", f"mau{i}.png") for i in range(1, 11)]
        source_frames = frames or []
        if not source_frames:
            for path in frame_paths or default_paths:
                source_frames.append(pygame.image.load(path))
        self.frames = [pygame.transform.scale(frame.convert_alpha(), size) for frame in source_frames]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.animation_speed = 0.1  # Tốc độ chuyển đổi khung hình (giây)
        self.time_since_last_frame = 0
        # bounce parameters (spawn bounce)
        self.initial_jump = -420.0
        self.max_bounces = 2
        self.bounce_dampings = [0.6, 0.4]

    def update(self, dt):
        # apply spawn bounce first
        _update_bounce(self, dt)
        # Cập nhật khung hình dựa trên thời gian
        self.time_since_last_frame += dt
        if self.time_since_last_frame >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.frames)  # Chuyển sang khung hình tiếp theo
            self.image = self.frames[self.current_frame]
            self.time_since_last_frame = 0

class Shield(pygame.sprite.Sprite):
    def __init__(self, x, y, frames=None, frame_dir=None, size=(32, 32), animation_speed=0.1):
        super().__init__()
        if frames or frame_dir:
            dir_path = frame_dir or os.path.join("assets", "hinh_anh", "khien")
            file_paths = frames or sorted(glob.glob(os.path.join(dir_path, "*.png")))
            self.frames = [pygame.transform.scale(pygame.image.load(fp).convert_alpha(), size) for fp in file_paths]
            self.current_frame = 0
            self.image = self.frames[0]
            self.rect = self.image.get_rect(topleft=(x, y))
            self.animation_speed = animation_speed
            self.time_since_last = 0.0
        else:
            surface = pygame.image.load(os.path.join("assets", "hinh_anh", "khien.png"))
            self.image = pygame.transform.scale(surface.convert_alpha(), size)
            self.rect = self.image.get_rect(topleft=(x, y))

        # bounce params (applies regardless of which branch was used)
        self.initial_jump = -420.0
        self.max_bounces = 2
        self.bounce_dampings = [0.6, 0.4]

    def update(self, dt):
        # bounce movement
        _update_bounce(self, dt)
        if hasattr(self, "frames"):
            self.time_since_last += dt
            if self.time_since_last >= self.animation_speed:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                center = self.rect.center
                self.image = self.frames[self.current_frame]
                self.rect = self.image.get_rect(center=center)
                self.time_since_last = 0.0

class DanItem(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface=None, image_path=None, size=(32, 32)):
        super().__init__()
        surface = image_surface or pygame.image.load(image_path or os.path.join("assets", "hinh_anh", "hop_dan.png"))
        self.image = pygame.transform.scale(surface.convert_alpha(), size)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        # bounce params - stronger pop for visible effect
        self.initial_jump = -480.0
        self.gravity = 1100.0
        self.max_bounces = 2
        self.bounce_dampings = [0.65, 0.35]

    def update(self, dt):
        _update_bounce(self, dt)

class TimeStop(pygame.sprite.Sprite):
    def __init__(self, x, y, frames=None, frame_dir=None, size=(32, 32), animation_speed=0.1):
        super().__init__()
        # Load all frames from timestop folder for animation
        dir_path = frame_dir or os.path.join("assets", "hinh_anh", "timestop")
        file_paths = frames or sorted(glob.glob(os.path.join(dir_path, "*.png")))
        self.frames = [pygame.transform.scale(pygame.image.load(fp).convert_alpha(), size) for fp in file_paths]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.animation_speed = animation_speed
        self.time_since_last = 0.0
        # bounce params
        self.initial_jump = -520.0
        self.gravity = 1100.0
        self.max_bounces = 2
        self.bounce_dampings = [0.7, 0.35]

    def update(self, dt):
        _update_bounce(self, dt)
        # Cập nhật khung hình dựa trên thời gian
        self.time_since_last += dt
        if self.time_since_last >= self.animation_speed:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            center = self.rect.center
            self.image = self.frames[self.current_frame]
            self.rect = self.image.get_rect(center=center)
            self.time_since_last = 0.0

class DamageBoost(pygame.sprite.Sprite):
    def __init__(self, x, y, image_surface=None, image_path=None, size=(32, 32)):
        super().__init__()
        surface = image_surface
        if surface is None and image_path:
            try:
                surface = pygame.image.load(image_path)
            except Exception:
                surface = None
        if surface is None:
            # Draw a simple lightning/fallback icon like before
            surface = pygame.Surface(size, pygame.SRCALPHA)
            surface.fill((0, 0, 0, 0))
            center = (size[0] // 2, size[1] // 2)
            radius = min(size) // 2 - 2
            pygame.draw.circle(surface, (255, 208, 0), center, radius)
            pygame.draw.circle(surface, (200, 120, 0), center, radius, 3)
            lightning = [
                (center[0] - 4, center[1] - 8),
                (center[0] + 2, center[1] - 2),
                (center[0] - 1, center[1] - 2),
                (center[0] + 4, center[1] + 8),
                (center[0] - 2, center[1] + 2),
                (center[0] + 1, center[1] + 2),
            ]
            pygame.draw.polygon(surface, (255, 255, 255), lightning)
        # Use a static image but apply the same bounce/spawn behavior as other items
        self.image = pygame.transform.scale(surface.convert_alpha(), size)
        self.rect = self.image.get_rect(topleft=(x, y))
        # bounce params (use strong pop for visibility)
        self.initial_jump = -480.0
        self.gravity = 1100.0
        self.max_bounces = 2
        self.bounce_dampings = [0.65, 0.35]

    def update(self, dt):
        # behave like other items: spawn bounce, no rotation
        _update_bounce(self, dt)