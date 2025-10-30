# map.py
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

import pygame
import random

from cau_hinh import (
    MAP_WIDTH, 
    MAP_HEIGHT,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
    RONG,
    CAO,
    BAN_DO_RONG,
    BAN_DO_CAO
)


def random_position_in_playable_area(margin=50):
    """Tra ve vi tri ngau nhien trong vung map co the choi (khong bao gom vien den)"""
    x = random.randint(MAP_PLAYABLE_LEFT + margin, MAP_PLAYABLE_RIGHT - margin)
    y = random.randint(MAP_PLAYABLE_TOP + margin, MAP_PLAYABLE_BOTTOM - margin)
    return x, y


def is_position_valid(x, y, obstacles, min_distance=60):
    """Kiem tra xem vi tri co va cham voi vat can hay khong
    min_distance: khoang cach toi thieu tu vat can (pixel)
    """
    test_rect = pygame.Rect(x - min_distance//2, y - min_distance//2, min_distance, min_distance)
    for vat_can in obstacles:
        if test_rect.colliderect(vat_can.rect):
            return False
    return True


def choose_spawn_position(prob_center=0.35, center_radius=150, margin=50, obstacles=None):
    """Chon vi tri spawn: voi xac suat prob_center chon gan center cua vung choi,
    nguoc lai chon ngau nhien trong playable area.
    center_radius: ban kinh (pixel) quanh tam noi item co the xuat hien.
    margin: khoang cach so voi bien playable khi chon random toan vung.
    obstacles: danh sach vat can de kiem tra va cham.
    """
    max_attempts = 30  # Toi da 30 lan thu tim vi tri hop le
    
    if random.random() < prob_center:
        # Chon tu center
        for _ in range(max_attempts):
            cx = (MAP_PLAYABLE_LEFT + MAP_PLAYABLE_RIGHT) // 2
            cy = (MAP_PLAYABLE_TOP + MAP_PLAYABLE_BOTTOM) // 2
            rx = random.randint(-center_radius, center_radius)
            ry = random.randint(-center_radius, center_radius)
            x = cx + rx
            y = cy + ry
            # clamp to playable area
            x = max(MAP_PLAYABLE_LEFT + margin, min(x, MAP_PLAYABLE_RIGHT - margin))
            y = max(MAP_PLAYABLE_TOP + margin, min(y, MAP_PLAYABLE_BOTTOM - margin))
            
            # Kiem tra neu khong va cham vat can thi dung
            if obstacles is None or is_position_valid(x, y, obstacles):
                return x, y
    else:
        # Chon ngau nhien
        for _ in range(max_attempts):
            x = random.randint(MAP_PLAYABLE_LEFT + margin, MAP_PLAYABLE_RIGHT - margin)
            y = random.randint(MAP_PLAYABLE_TOP + margin, MAP_PLAYABLE_BOTTOM - margin)
            
            # Kiem tra neu khong va cham vat can thi dung
            if obstacles is None or is_position_valid(x, y, obstacles):
                return x, y
    
    # Neu khong tim duoc vi tri hop le sau max_attempts, tra ve ngau nhien
    return random_position_in_playable_area(margin)


def tao_camera_rect(target_rect):
    """Tao camera rect de theo doi target"""
    half_w = RONG // 2
    half_h = CAO // 2
    x = target_rect.centerx - half_w
    y = target_rect.centery - half_h
    max_x = max(0, BAN_DO_RONG - RONG)
    max_y = max(0, BAN_DO_CAO - CAO)
    x = max(0, min(x, max_x))
    y = max(0, min(y, max_y))
    return pygame.Rect(int(x), int(y), RONG, CAO)


def ve_nhom(group, surface, offset):
    """Ve tat ca sprite trong nhom voi offset camera"""
    ox, oy = offset
    for sprite in group:
        surface.blit(sprite.image, sprite.rect.move(ox, oy))


class GameMap:
    def __init__(self, project_dir):
        self._path = os.path.join(project_dir, "assets", "map", "map.png")
        self.surface = self._load_surface()
        self.rect = self.surface.get_rect()

    def _load_surface(self):
        try:
            surface = pygame.image.load(self._path).convert()
        except FileNotFoundError:
            surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
            surface.fill((20, 20, 30))
            return surface
        if surface.get_size() != (MAP_WIDTH, MAP_HEIGHT):
            surface = pygame.transform.smoothscale(surface, (MAP_WIDTH, MAP_HEIGHT))
        return surface

    def draw(self, target, camera_rect):
        target.blit(self.surface, (0, 0), area=camera_rect)

    @property
    def size(self):
        return self.surface.get_size()
