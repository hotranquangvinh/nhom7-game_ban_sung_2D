# huong_dan_wave.py - Hướng dẫn tích hợp hệ thống wave vào main.py

"""
HƯỚNG DẪN TÍCH HỢP HỆ THỐNG WAVE VÀO MAIN.PY:

1. Import WaveManager ở đầu file main.py:
   
   from dot import WaveManager

2. Khởi tạo WaveManager sau khi khởi tạo người chơi và các nhóm sprite:
   
   # Tạo wave manager
   wave_manager = WaveManager(nguoi_choi, tat_ca_sprite, nhom_dan, item_manager)
   
   # Bắt đầu đợt 1
   wave_manager.start_wave(0)

3. Trong game loop, cập nhật wave manager (thay vì sinh quái tự động):
   
   # Cập nhật wave (sử dụng dt nếu có, hoặc update() nếu không)
   wave_manager.update_with_dt(dt)  # hoặc wave_manager.update()

4. VẼ THÔNG BÁO chuyển đợt lên màn hình (trong phần vẽ):
   
   # Vẽ thông báo chuyển đợt (nếu có)
   wave_manager.draw_transition_message(man_hinh, phong_chu)

5. Hiển thị thông tin wave trên UI (tùy chọn):
   
   info = wave_manager.get_current_wave_info()
   
   # Vẽ thông tin wave
   wave_text = phong_chu.render(
       f"Đợt {info['wave_number']}: {info['enemies_remaining']}/{info['total_enemies']}",
       True, (255, 255, 255)
   )
   man_hinh.blit(wave_text, (10, 60))

6. XÓA hoặc COMMENT các đoạn code sinh quái tự động cũ:
   
   # XÓA hoặc comment code như thế này:
   # if thoi_gian_dem >= ENEMY_SPAWN_INTERVAL:
   #     thoi_gian_dem = 0
   #     spawn_enemy(...)

VÍ DỤ CODE HOÀN CHỈNH TRONG MAIN.PY:

# ===== Ở đầu file =====
from dot import WaveManager

# ===== Sau khi khởi tạo người chơi =====
wave_manager = WaveManager(nguoi_choi, tat_ca_sprite, nhom_dan, item_manager)
wave_manager.start_wave(0)  # Bắt đầu đợt 1

# ===== Trong game loop (phần update) =====
while dang_choi:
    dt = dong_ho.tick(FPS) / 1000.0
    
    # ... các code khác ...
    
    # Cập nhật wave
    wave_manager.update_with_dt(dt)
    
    # Hoặc nếu không có dt:
    # wave_manager.update()
    
    # ... các code khác ...

# ===== Trong phần vẽ (render) =====
    # Vẽ tất cả sprite
    ve_nhom(tat_ca_sprite, man_hinh, offset)
    
    # Vẽ UI
    ve_ui(man_hinh, nguoi_choi, phong_chu)
    
    # Vẽ thông tin wave
    info = wave_manager.get_current_wave_info()
    wave_text = phong_chu.render(
        f"Đợt {info['wave_number']}: {info['enemies_remaining']}/{info['total_enemies']}",
        True, (255, 255, 255)
    )
    man_hinh.blit(wave_text, (10, 60))
    
    # VẼ THÔNG BÁO CHUYỂN ĐỢT (QUAN TRỌNG!)
    wave_manager.draw_transition_message(man_hinh, phong_chu)
    
    pygame.display.flip()

LƯU Ý:
- Hệ thống tự động chuyển đợt sau khi tiêu diệt hết quái
- Có thời gian chờ 3 giây giữa các đợt với countdown
- Thông báo hiển thị tự động khi chuyển đợt
- Không cần gọi next_wave() thủ công nữa
"""
