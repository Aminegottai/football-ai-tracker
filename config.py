# ══════════════════════════════════════════════════════
# CONFIGURATION CENTRALISÉE
# ══════════════════════════════════════════════════════

# ── Chemins ────────────────────────────────────────────
MODEL_PATH = r'C:\Users\amine\Downloads\bestr.pt'
VIDEO_PATH = r'C:\Users\amine\AppData\Local\CapCut\Videos\t.mp4'

# ── FPS par défaut ─────────────────────────────────────
DEFAULT_FPS = 30.0

# ── TRACKER ────────────────────────────────────────────
TRACKER_MAX_LOST = 30
TRACKER_MIN_IOU = 0.20

# ── CLASSIFIER GMM ─────────────────────────────────────
GMM_N_COMPONENTS = 2
GMM_COVARIANCE_TYPE = 'full'
GMM_N_INIT = 25
GMM_MAX_ITER = 300
GMM_REG_COVAR = 1e-3
GMM_LOCK_THRESHOLD = 0.80
GMM_MIN_VOTES = 20

# ── POSSESSION ─────────────────────────────────────────
POSSESSION_CONFIRM_FRAMES = 8
POSSESSION_MIN_HOLD_FRAMES = 12
POSSESSION_MAX_DIST_PX = 120
POSSESSION_WINDOW_SECONDS = 30

# ── DÉTECTION ──────────────────────────────────────────
DETECTION_CONF = 0.3
JERSEY_COLOR_Y_RANGE = (0.15, 0.55)  # % hauteur
JERSEY_COLOR_X_RANGE = (0.10, 0.90)  # % largeur

# ── CALIBRATION ───────────────────────────────────────
CALIB_MAX_FRAMES = 80
CALIB_MIN_COLORS = 30

# ── DASHBOARD ──────────────────────────────────────────
DASHBOARD_WIDTH = 820
DASHBOARD_HEIGHT = 680

# Couleurs BGR
BG_DARK = (15, 15, 20)
BG_CARD = (25, 28, 35)
BG_CARD2 = (32, 36, 45)
BORDER = (55, 60, 75)
GOLD = (40, 200, 255)
WHITE = (240, 240, 245)
GRAY = (130, 135, 145)
GRAY_DARK = (60, 65, 75)
GREEN_N = (50, 230, 120)

# ── FENÊTRES ───────────────────────────────────────────
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720
CAMERA_X = 0
CAMERA_Y = 0

DASHBOARD_POS_X = 1290
DASHBOARD_POS_Y = 0

# ── DEBUG ──────────────────────────────────────────────
DEBUG_MODE = False
VERBOSE = True