# cau_hinh.py - Cấu hình trò chơi

# Kích thước và tốc độ khung hình
RONG = 960   # Chiều rộng cửa sổ hiển thị
CAO = 600    # Chiều cao cửa sổ hiển thị
SO_KHUNG_HINH = 60  # Số khung hình mỗi giây

# Kích thước bản đồ (lớn hơn cửa sổ)
BAN_DO_RONG = 2000  # Kích thước ảnh đầy đủ
BAN_DO_CAO = 1666   # Kích thước ảnh đầy đủ

# Giới hạn vùng chơi thực tế (loại trừ viền đen và tường trong ảnh map)
MAP_PLAYABLE_LEFT = 399
MAP_PLAYABLE_TOP = 370    # Tăng lên để tránh vùng tường phía trên (tường kết thúc ở ~360)
MAP_PLAYABLE_RIGHT = 1600
MAP_PLAYABLE_BOTTOM = 1267
MAP_PLAYABLE_WIDTH = MAP_PLAYABLE_RIGHT - MAP_PLAYABLE_LEFT
MAP_PLAYABLE_HEIGHT = MAP_PLAYABLE_BOTTOM - MAP_PLAYABLE_TOP

# Alias bản đồ để tương thích với mã tiếng Anh
MAP_WIDTH = BAN_DO_RONG
MAP_HEIGHT = BAN_DO_CAO

# Thời gian sinh kẻ thù
KHOANG_SINH_KE_THU = 2.0  # Thời gian giữa các lần sinh kẻ thù (giây)

# Cài đặt người chơi
TOC_DO_NGUOI_CHOI = 300        # px/giây (nếu dùng ở nơi khác)
MAU_TOI_DA_NGUOI_CHOI = 3
SUC_CHUA_BANG_DAN = 20         # Sức chứa 1 băng
DAN_DU_TRU_TOI_DA = 30         # Đạn dự trữ tối đa

# Nạp đạn
THOI_GIAN_NAP_DAN = 1.5        # giây

# Đạn
TOC_DO_DAN = 300               # px/giây
TOC_DO_DAN_KE_THU = 180        # px/giây (tốc độ đạn kẻ thù chậm hơn để dễ né)

# Kẻ thù
TOC_DO_KE_THU = 50             # px/giây
KHOANG_BAN_KE_THU_TOI_THIEU = 1.2
KHOANG_BAN_KE_THU_TOI_DA = 3.0
ENEMY_SPEED = 40  # tốc độ kẻ thù chậm lại

# Alias giữ tương thích với mã hiện tại (tiếng Anh)
WIDTH = RONG
HEIGHT = CAO
FPS = SO_KHUNG_HINH

ENEMY_SPAWN_INTERVAL = KHOANG_SINH_KE_THU

PLAYER_SPEED = 200  # tốc độ người chơi nhanh lên xíu
PLAYER_MAX_HP = MAU_TOI_DA_NGUOI_CHOI
PLAYER_MAGAZINE = SUC_CHUA_BANG_DAN
PLAYER_RESERVE_MAX = DAN_DU_TRU_TOI_DA

RELOAD_TIME = THOI_GIAN_NAP_DAN

BULLET_SPEED = TOC_DO_DAN
ENEMY_BULLET_SPEED = TOC_DO_DAN_KE_THU

ENEMY_SPEED = TOC_DO_KE_THU
ENEMY_SHOOT_INTERVAL_MIN = KHOANG_BAN_KE_THU_TOI_THIEU
ENEMY_SHOOT_INTERVAL_MAX = KHOANG_BAN_KE_THU_TOI_DA

# Đường dẫn hình ảnh vật phẩm
HINH_MEDKIT = "assets/hinh_anh/mau.jpg"
HINH_SHIELD = "assets/hinh_anh/khien.png"  # Đường dẫn hình ảnh Khiên
HINH_TIMESTOP = r"assets\hinh_anh\timestop.png"  # Đường dẫn hình ảnh TimeStop
HINH_DAMAGE_BOOST = r"assets\hinh_anh\damage_boost.png"  # Đường dẫn hình ảnh Damage Boost
HINH_DAN = "assets/hinh_anh/hop_dan.png"

# Vật cản
SO_VAT_CAN = 5
VAT_CAN_THU_MUC = "assets/vatcan"
VAT_CAN_KHOANG_CACH = 200  # khoảng trống tối thiểu giữa vật cản, người chơi và kẻ thù khi spawn
VAT_CAN_SCALE = 0.45  # tăng kích thước vật cản rõ rệt
