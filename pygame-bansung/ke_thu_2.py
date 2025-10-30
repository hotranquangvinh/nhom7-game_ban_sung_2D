# ke_thu_2.py - Kẻ thù cận chiến (melee enemy)
import os
import pygame, random
from cau_hinh import (
    ENEMY_SPEED,
    MAP_PLAYABLE_LEFT,
    MAP_PLAYABLE_TOP,
    MAP_PLAYABLE_RIGHT,
    MAP_PLAYABLE_BOTTOM,
)
from ke_thu import load_animation_frames


class MeleeEnemy(pygame.sprite.Sprite):
    """
    Kẻ thù cận chiến: di chuyển nhanh về phía người chơi và tấn công cận chiến.
    Không bắn đạn mà gây sát thương khi va chạm trực tiếp.
    """
    def __init__(self, vi_tri, muc_tieu_nguoi_choi, nhom_tat_ca_sprite, item_manager=None):
        super().__init__()
        # Stun state
        self.is_stunned = False
        self.stun_timer = 0.0
        self.stun_duration = 1.0
        
        # Load animation từ assets/ke_thu_2
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets', 'ke_thu_2')
        self.anim = load_animation_frames(assets_folder)
        
        # Scale animation frames to 90% (larger than before)
        try:
            scale = 0.9
            for k, frames in list(self.anim.items()):
                scaled = []
                for f in frames:
                    try:
                        w = int(f.get_width() * scale)
                        h = int(f.get_height() * scale)
                        if w > 0 and h > 0:
                            sf = pygame.transform.smoothscale(f, (w, h))
                        else:
                            sf = f
                    except Exception:
                        sf = f
                    scaled.append(sf)
                self.anim[k] = scaled
        except Exception:
            pass
        
        # Fallback nếu không có frames
        if not any(self.anim.values()):
            surf = pygame.Surface((40, 40))
            surf.fill((200, 100, 50))  # Màu cam để phân biệt với kẻ thù thường
            self.anim['idle'] = [surf]
        
        # Animation state
        self.state = 'idle'
        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_duration = 0.12  # Điều chỉnh tốc độ animation cho mượt mà hơn
        
        # Initial image and rect
        first = self.anim.get('idle')[0] if self.anim.get('idle') else list(next(iter(self.anim.values())))[0]
        self.image = first
        self.rect = self.image.get_rect(center=vi_tri)
        
        # References
        self.muc_tieu = muc_tieu_nguoi_choi
        self.nhom_tat_ca = nhom_tat_ca_sprite
        self.item_manager = item_manager
        
        # Combat attributes
        self.hp = 3  # Cần 3 đạn để tiêu diệt
        self.hp_toi_da = 3  # Maximum HP for health bar
        self.toc_do = ENEMY_SPEED * 1.1  # Chỉ nhanh hơn 10% so với kẻ thù thường
        
        # Movement - luôn hướng về player
        self.huong = pygame.Vector2(1, 0)
        self.update_direction_timer = 0.0
        self.update_direction_interval = 0.3  # Cập nhật hướng thường xuyên
        
        # Melee attack
        self.attack_range = 60  # Khoảng cách để bắt đầu tấn công
        self.attack_cooldown = 1.5  # Giảm tốc độ tấn công (tăng thời gian giữa các đòn)
        self.attack_timer = 0.0
        self.is_attacking = False
        self.attack_damage = 1
        
        # Mark as melee enemy (not boss)
        self.is_melee = True
        self.last_touch_ticks = -999999  # Khởi tạo để va chạm có thể xảy ra ngay
    
    def set_state(self, s):
        if s == self.state:
            return
        # Once dead, don't change state
        if getattr(self, 'state', None) == 'dead' and s != 'dead':
            return
        self.state = s
        self.frame_index = 0
        self.frame_timer = 0.0
        if s == 'shoot':  # 'shoot' state sẽ được dùng cho melee attack animation
            self.is_attacking = True
    
    def update_animation(self, dt):
        frames = self.anim.get(self.state) or self.anim.get('idle')
        if not frames:
            return
        self.frame_timer += dt
        if self.frame_timer >= self.frame_duration:
            self.frame_timer -= self.frame_duration
            self.frame_index += 1
            if self.frame_index >= len(frames):
                if self.state == 'shoot':  # Melee attack animation done
                    self.is_attacking = False
                    self.set_state('run')  # Quay về chạy
                    frames = self.anim.get(self.state) or frames
                elif self.state == 'dead':
                    # End of dead animation
                    self.kill()
                    return
                else:
                    # Loop
                    self.frame_index = 0
        
        # Get current frame and flip if needed
        current = frames[self.frame_index % len(frames)]
        if self.huong.x < 0:
            self.image = pygame.transform.flip(current, True, False)
        else:
            self.image = current
    
    def _move_axis(self, delta, obstacles, axis="x"):
        """Di chuyển theo một trục với kiểm tra va chạm vật cản."""
        if delta == 0:
            return False

        if axis == "x":
            self.rect.x += delta
        else:
            self.rect.y += delta

        collided = False
        for vat_can in obstacles:
            if not self.rect.colliderect(vat_can.rect):
                continue
            collided = True
            if axis == "x":
                if delta > 0:
                    self.rect.right = vat_can.rect.left
                else:
                    self.rect.left = vat_can.rect.right
            else:
                if delta > 0:
                    self.rect.bottom = vat_can.rect.top
                else:
                    self.rect.top = vat_can.rect.bottom
        return collided

    def update(self, dt, vat_cans=None):
        # If dead, only animate
        if self.state == 'dead':
            self.update_animation(dt)
            return

        # Respect timestop freeze: if freeze_end is set and in the future, do nothing
        try:
            now_ms = pygame.time.get_ticks()
            if getattr(self, 'freeze_end', 0) > now_ms:
                # do not move, attack, or animate while frozen
                return
        except Exception:
            pass

        # Nếu bị stun thì chỉ đếm timer và đứng yên
        if self.is_stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.is_stunned = False
                self.set_state('run')
            self.update_animation(dt)
            return
        
        # Update attack timer
        self.attack_timer = max(0.0, self.attack_timer - dt)
        
        # Update direction toward player
        self.update_direction_timer += dt
        if self.update_direction_timer >= self.update_direction_interval and self.muc_tieu:
            self.update_direction_timer = 0.0
            dx = self.muc_tieu.rect.centerx - self.rect.centerx
            dy = self.muc_tieu.rect.centery - self.rect.centery
            vec = pygame.Vector2(dx, dy)
            if vec.length() > 0:
                self.huong = vec.normalize()
        
        # Check distance to player for melee attack
        if self.muc_tieu and not self.is_attacking:
            dx = self.muc_tieu.rect.centerx - self.rect.centerx
            dy = self.muc_tieu.rect.centery - self.rect.centery
            distance = (dx*dx + dy*dy) ** 0.5
            
            if distance <= self.attack_range and self.attack_timer <= 0.0:
                # Trigger melee attack animation
                self.set_state('shoot')  # Use 'shoot' state for attack animation
                self.attack_timer = self.attack_cooldown
            elif not self.is_attacking:
                # Keep running toward player
                self.set_state('run')
        
        obstacles = vat_cans if vat_cans is not None else ()

        # Move (slower during attack animation)
        if self.is_attacking:
            # Slow down during attack
            dx = self.huong.x * self.toc_do * dt * 0.3
            dy = self.huong.y * self.toc_do * dt * 0.3
        else:
            dx = self.huong.x * self.toc_do * dt
            dy = self.huong.y * self.toc_do * dt
        
        self._move_axis(dx, obstacles, axis="x")
        self._move_axis(dy, obstacles, axis="y")
        
        # Keep in playable map bounds
        vung = pygame.Rect(
            MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_TOP,
            MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT,
            MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP,
        )
        self.rect.clamp_ip(vung)
        
        # Update animation
        self.update_animation(dt)
    
    def take_damage(self, amount=1):
        self.hp -= amount
        if self.hp <= 0:
            self.set_state('dead')
        else:
            # Bị khựng lại 1 giây
            self.is_stunned = True
            self.stun_timer = self.stun_duration
            self.set_state('idle')
    
    def ve_thanh_mau(self, man_hinh, offset):
        """Vẽ thanh máu phía trên đầu kẻ thù"""
        if self.hp <= 0:
            return  # Don't draw health bar if dead
        
        # Health bar dimensions
        bar_width = 40
        bar_height = 4
        bar_x = self.rect.centerx - bar_width // 2 - offset[0]
        bar_y = self.rect.top - 10 - offset[1]
        
        # Background (red)
        pygame.draw.rect(man_hinh, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Foreground (green) - current HP
        current_width = int((self.hp / self.hp_toi_da) * bar_width)
        if current_width > 0:
            pygame.draw.rect(man_hinh, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))
    
    # Alias for compatibility
    nhan_sat_thuong = take_damage
    cap_nhat = update

