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
except ModuleNotFoundError as exc:  # pragma: no cover - friendly exit if pygame missing
    raise SystemExit("Thiếu pygame. Hãy chạy 'pip install pygame' trong môi trường ảo rồi thử lại.") from exc
import random

from cau_hinh import (
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
    VAT_CAN_KHOANG_CACH
)


class VatCan(pygame.sprite.Sprite):
    def __init__(self, image_surface: pygame.Surface, topleft: tuple[int, int]):
        super().__init__()
        # Sao chép để tránh chia sẻ surface gốc giữa các instance
        self.image = image_surface.copy()
        self.rect = self.image.get_rect(topleft=topleft)


def tai_hinh_vat_can(thu_muc: str, scale: float = 1.0) -> list[pygame.Surface]:
    """Tải toàn bộ ảnh vật cản từ thư mục (png/jpg/bmp) và thu nhỏ nếu cần."""
    if not thu_muc or not os.path.isdir(thu_muc):
        return []

    ket_qua: list[pygame.Surface] = []
    for ten in sorted(os.listdir(thu_muc)):
        lower = ten.lower()
        if not lower.endswith((".png", ".jpg", ".jpeg", ".bmp")):
            continue
        duong_dan = os.path.join(thu_muc, ten)
        try:
            be_mat = pygame.image.load(duong_dan).convert_alpha()
        except FileNotFoundError:
            continue
        # Allow specific obstacle images (thung1/thung2) to be smaller than the global scale
        local_scale = scale if scale is not None else 1.0
        try:
            if lower.startswith('thung1') or lower.startswith('thung2') or 'thung1' in lower or 'thung2' in lower:
                # make these containers smaller (e.g. 60% of the configured scale)
                local_scale = (scale if scale is not None else 1.0) * 0.6
        except Exception:
            local_scale = scale

        if local_scale and local_scale != 1.0:
            rong = max(1, int(be_mat.get_width() * local_scale))
            cao = max(1, int(be_mat.get_height() * local_scale))
            be_mat = pygame.transform.smoothscale(be_mat, (rong, cao))
        ket_qua.append(be_mat)
    return ket_qua


def khoi_tao_vat_can(vat_cans_group, vat_can_images, so_vat_can, avoid_rects=None):
    """Tao moi cac vat can voi vi tri ngau nhien trong vung map co the choi.
    
    Args:
        vat_cans_group: Sprite group chua vat can
        vat_can_images: List cac hinh anh vat can
        so_vat_can: So luong vat can can tao
        avoid_rects: List cac rect can tranh (vi du vi tri nguoi choi)
    """
    vat_cans_group.empty()
    if not vat_can_images:
        return

    so_vat_can = max(1, so_vat_can)
    if len(vat_can_images) >= so_vat_can:
        hinh_duoc_chon = random.sample(vat_can_images, so_vat_can)
    else:
        hinh_duoc_chon = [random.choice(vat_can_images) for _ in range(so_vat_can)]

    truc_tranh = list(avoid_rects or [])
    margin = max(0, VAT_CAN_KHOANG_CACH)

    for be_mat in hinh_duoc_chon:
        rong, cao = be_mat.get_size()
        # Chi spawn trong vung map thuc te (khong spawn o vung den)
        min_x = MAP_PLAYABLE_LEFT
        max_x = max(min_x, MAP_PLAYABLE_RIGHT - rong)
        min_y = MAP_PLAYABLE_TOP
        max_y = max(min_y, MAP_PLAYABLE_BOTTOM - cao)
        
        dat_duoc = None
        for _ in range(40):
            x = random.randint(min_x, max_x)
            y = random.randint(min_y, max_y)
            rect = pygame.Rect(x, y, rong, cao)
            inflated = rect.inflate(margin, margin) if margin else rect
            if any(rect.colliderect(vat_can.rect) for vat_can in vat_cans_group):
                continue
            if any(inflated.colliderect(vung) for vung in truc_tranh):
                continue
            dat_duoc = rect
            break
        if dat_duoc is None:
            dat_duoc = pygame.Rect(random.randint(min_x, max_x), random.randint(min_y, max_y), rong, cao)
        vat_cans_group.add(VatCan(be_mat, dat_duoc.topleft))
        truc_tranh.append(dat_duoc.inflate(margin, margin))
