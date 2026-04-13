import cv2
import numpy as np
import config

# ══════════════════════════════════════════════════════
# DASHBOARD PROFESSIONNEL
# ══════════════════════════════════════════════════════

class FootballDashboard:
    """
    Rendu visuel du dashboard avec statistiques de possession.
    """
    
    DW = config.DASHBOARD_WIDTH
    DH = config.DASHBOARD_HEIGHT
    
    BG_DARK = config.BG_DARK
    BG_CARD = config.BG_CARD
    BG_CARD2 = config.BG_CARD2
    BORDER = config.BORDER
    GOLD = config.GOLD
    WHITE = config.WHITE
    GRAY = config.GRAY
    GRAY_DARK = config.GRAY_DARK
    GREEN_N = config.GREEN_N

    def __init__(self):
        self.canvas = None

    def _make_canvas(self):
        return np.full((self.DH, self.DW, 3),
                       self.BG_DARK, dtype=np.uint8)

    def _rect(self, img, x, y, w, h, color, radius=8, fill=True):
        """Dessine un rectangle arrondi."""
        if fill:
            cv2.rectangle(img, (x + radius, y), (x + w - radius, y + h), color, -1)
            cv2.rectangle(img, (x, y + radius), (x + w, y + h - radius), color, -1)
            for cx, cy in [(x + radius, y + radius), (x + w - radius, y + radius),
                          (x + radius, y + h - radius), (x + w - radius, y + h - radius)]:
                cv2.circle(img, (cx, cy), radius, color, -1)
        else:
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 1)

    def _text(self, img, txt, x, y, scale, color,
              bold=False, center=False):
        """Dessine du texte."""
        thick = 2 if bold else 1
        if center:
            (tw, _), _ = cv2.getTextSize(
                txt, cv2.FONT_HERSHEY_SIMPLEX, scale, thick)
            x -= tw // 2
        cv2.putText(img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, scale, color,
                    thick, cv2.LINE_AA)

    def _gradient_bar(self, img, x, y, w, h, c1, c2):
        """Dessine une barre dégradée."""
        for i in range(w):
            t = i / max(w - 1, 1)
            col = tuple(int(c1[j] * (1 - t) + c2[j] * t) for j in range(3))
            cv2.line(img, (x + i, y), (x + i, y + h), col, 1)

    def _draw_header(self, img, elapsed, fps, calibrated):
        """Header avec titre et informations."""
        self._rect(img, 0, 0, self.DW, 70, (20, 22, 30))
        cv2.rectangle(img, (0, 68), (self.DW, 71), self.GOLD, -1)
        self._text(img, "FOOTBALL ANALYZER", 30, 45,
                   0.85, self.GOLD, bold=True)

        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self._text(img, "TEMPS VIDÉO",
                   self.DW // 2 - 55, 25, 0.40, self.GRAY)
        self._text(img, f"{mins:02d}:{secs:02d}",
                   self.DW // 2 - 38, 55, 1.1, self.WHITE, bold=True)

        col = self.GREEN_N if calibrated else (0, 180, 255)
        txt = "EN DIRECT" if calibrated else "CALIBRATION"
        self._rect(img, self.DW - 180, 15, 160, 40, (35, 38, 50), radius=6)
        cv2.circle(img, (self.DW - 160, 35), 6, col, -1)
        self._text(img, txt, self.DW - 148, 40, 0.45, col)
        self._text(img, f"FPS {fps:.0f}", self.DW - 80, 40,
                   0.42, self.GRAY)

    def _draw_scoreboard(self, img, team_bgr, tracker):
        """Scoreboard possession principal."""
        X, Y, W, H = 20, 85, self.DW - 40, 110
        self._rect(img, X, Y, W, H, self.BG_CARD, radius=10)
        cv2.rectangle(img, (X, Y + H - 3), (X + W, Y + H), self.GOLD, -1)

        col1 = team_bgr.get(1, (80, 200, 80))
        col2 = team_bgr.get(2, (80, 80, 200))
        p1t, p2t = tracker.get_time_possession()
        t1s, t2s = tracker.get_time_str()

        # Equipe 1
        self._rect(img, X + 10, Y + 10, W // 2 - 30, H - 20, col1, radius=8)
        ov = img.copy()
        self._rect(ov, X + 10, Y + 10, W // 2 - 30, H - 20, (0, 0, 0), radius=8)
        cv2.addWeighted(ov, 0.45, img, 0.55, 0, img)
        self._text(img, "EQUIPE  1", X + 20, Y + 38,
                   0.55, self.WHITE, bold=True)
        cv2.circle(img, (X + W // 2 - 50, Y + 35), 12, col1, -1)
        self._text(img, f"{p1t:.1f}%", X + 20, Y + 78,
                   1.3, col1, bold=True)
        self._text(img, f"Temps: {t1s}", X + 20, Y + 102,
                   0.48, self.GRAY)

        # Equipe 2
        mid = X + W // 2
        self._text(img, "VS", mid - 15, Y + H // 2 + 8,
                   0.8, self.GRAY, bold=True)
        self._rect(img, mid + 20, Y + 10, W // 2 - 30, H - 20, col2, radius=8)
        ov = img.copy()
        self._rect(ov, mid + 20, Y + 10, W // 2 - 30, H - 20, (0, 0, 0), radius=8)
        cv2.addWeighted(ov, 0.45, img, 0.55, 0, img)
        self._text(img, "EQUIPE  2", mid + 30, Y + 38,
                   0.55, self.WHITE, bold=True)
        cv2.circle(img, (mid + W // 2 - 30, Y + 35), 12, col2, -1)
        self._text(img, f"{p2t:.1f}%", mid + 30, Y + 78,
                   1.3, col2, bold=True)
        self._text(img, f"Temps: {t2s}", mid + 30, Y + 102,
                   0.48, self.GRAY)

    def _draw_possession_section(self, img, tracker, team_bgr):
        """Section possession du ballon."""
        X, Y = 20, 215
        W = self.DW - 40
        self._text(img, "POSSESSION DU BALLON",
                   X, Y + 18, 0.55, self.GOLD, bold=True)
        cv2.line(img, (X, Y + 25), (X + W, Y + 25), self.BORDER, 1)

        col1 = team_bgr.get(1, (80, 200, 80))
        col2 = team_bgr.get(2, (80, 80, 200))
        t1s, t2s = tracker.get_time_str()

        self._dual_bar(img, X, Y + 38, W, 52,
                       *tracker.get_time_possession(), col1, col2,
                       "TEMPS EFFECTIF", t1s, t2s)

        p1p, p2p = tracker.get_pass_possession()
        self._dual_bar(img, X, Y + 100, W, 52,
                       *tracker.get_pass_possession(), col1, col2,
                       "PASSES RÉUSSIES",
                       str(tracker.passes[1]),
                       str(tracker.passes[2]))

        self._dual_bar(img, X, Y + 162, W, 52,
                       *tracker.get_window_possession(), col1, col2,
                       "30 DERNIÈRES SECONDES", "", "")

        f1, f2, f0 = tracker.get_possession_frames_raw()
        total = f1 + f2 + f0
        self._text(img,
                   f"frames: T1={f1} T2={f2} libre={f0} total={total}",
                   X, Y + 228, 0.35, self.GRAY_DARK)

    def _dual_bar(self, img, x, y, w, h,
                  p1, p2, c1, c2, title, ex1="", ex2=""):
        """Barre double pour comparaison."""
        self._rect(img, x, y, w, h, self.BG_CARD, radius=8)
        self._text(img, title, x + w // 2, y + 16, 0.42,
                   self.GRAY, center=True)

        BX = x + 95
        BY = y + 22
        BW = w - 195
        BH = 22
        cv2.rectangle(img, (BX, BY), (BX + BW, BY + BH),
                      self.BG_DARK, -1)

        w1 = int(BW * p1 / 100)
        if w1 > 0:
            self._gradient_bar(img, BX, BY, w1, BH, c1,
                              tuple(min(255, v + 40) for v in c1))
        if w1 < BW:
            self._gradient_bar(img, BX + w1, BY, BW - w1, BH,
                              tuple(min(255, v + 40) for v in c2), c2)

        cv2.line(img, (BX + w1, BY), (BX + w1, BY + BH),
                 (255, 255, 255), 2)
        cv2.rectangle(img, (BX, BY), (BX + BW, BY + BH), self.BORDER, 1)

        t1 = f"{p1:.1f}%"
        if ex1:
            t1 += f"  {ex1}"
        self._text(img, t1, x + 6, BY + BH - 4, 0.46, c1, bold=True)

        t2 = f"{p2:.1f}%"
        if ex2:
            t2 = f"{ex2}  " + t2
        (tw, _), _ = cv2.getTextSize(t2,
                                     cv2.FONT_HERSHEY_SIMPLEX, 0.46, 2)
        self._text(img, t2, x + w - tw - 6, BY + BH - 4, 0.46, c2, bold=True)

    def _draw_chart(self, img, x, y, w, h,
                    hist1, hist2, c1, c2, title):
        """Graphique historique."""
        self._rect(img, x, y, w, h, self.BG_CARD, radius=8)
        self._text(img, title, x + 10, y + 20, 0.46, self.GOLD, bold=True)
        if len(hist1) < 2:
            return

        GX = x + 35
        GY = y + 28
        GW = w - 45
        GH = h - 40

        for pct in [25, 50, 75]:
            gy2 = GY + GH - int(GH * pct / 100)
            cv2.line(img, (GX, gy2), (GX + GW, gy2),
                     self.GRAY_DARK, 1)
            self._text(img, f"{pct}", GX - 28, gy2 + 4,
                       0.30, self.GRAY_DARK)

        data1 = list(hist1)
        data2 = list(hist2)
        n = len(data1)
        
        for i in range(1, n):
            x1g = GX + int((i - 1) / max(n - 1, 1) * GW)
            x2g = GX + int(i / max(n - 1, 1) * GW)
            y1a = GY + GH - int(data1[i - 1] / 100 * GH)
            y2a = GY + GH - int(data1[i] / 100 * GH)
            cv2.line(img, (x1g, y1a), (x2g, y2a), c1, 2)
            y1b = GY + GH - int(data2[i - 1] / 100 * GH)
            y2b = GY + GH - int(data2[i] / 100 * GH)
            cv2.line(img, (x1g, y1b), (x2g, y2b), c2, 2)

        if data1:
            cv2.circle(img, (GX + GW,
                            GY + GH - int(data1[-1] / 100 * GH)), 5, c1, -1)
            cv2.circle(img, (GX + GW,
                            GY + GH - int(data2[-1] / 100 * GH)), 5, c2, -1)
            self._text(img, f"T1:{data1[-1]:.0f}%",
                       GX + GW - 65, GY + 14, 0.38, c1)
            self._text(img, f"T2:{data2[-1]:.0f}%",
                       GX + GW - 65, GY + 27, 0.38, c2)

    def _draw_cards(self, img, tracker, team_bgr,
                    n_locked, calib_pct):
        """Cards de statistiques."""
        X, Y = 20, 560
        CW, CH = 178, 72
        GAP = 12
        col1 = team_bgr.get(1, (80, 200, 80))
        col2 = team_bgr.get(2, (80, 80, 200))

        curr = tracker.current_team
        curr_txt = (f"EQUIPE {curr}" if curr > 0 else "LIBRE")
        curr_col = (team_bgr.get(curr, (130, 130, 130))
                    if curr > 0 else (100, 100, 100))

        p1p, p2p = tracker.get_pass_possession()
        cards = [
            ("T1  PASSES",
             f"{tracker.passes[1]}  ({p1p:.0f}%)", col1),
            ("T2  PASSES",
             f"{tracker.passes[2]}  ({p2p:.0f}%)", col2),
            ("BALLON", curr_txt, curr_col),
            ("IDENTIFIÉS", f"{n_locked} joueurs",
             (100, 210, 255)),
        ]
        
        for i, (title, val, col) in enumerate(cards):
            cx = X + i * (CW + GAP)
            self._rect(img, cx, Y, CW, CH, self.BG_CARD, radius=8)
            self._rect(img, cx, Y, CW, 5, col, radius=4)
            self._text(img, title, cx + 10, Y + 23, 0.38, self.GRAY)
            self._text(img, val, cx + 10, Y + 55, 0.75, col, bold=True)

        if calib_pct < 1.0:
            cx = X + 4 * (CW + GAP)
            self._rect(img, cx, Y, CW, CH, self.BG_CARD, radius=8)
            self._rect(img, cx, Y, CW, 5, (0, 180, 255), radius=4)
            self._text(img, "CALIBRATION", cx + 10, Y + 23,
                       0.38, self.GRAY)
            bw = CW - 20
            cv2.rectangle(img, (cx + 10, Y + 34),
                          (cx + 10 + bw, Y + 50), self.BG_DARK, -1)
            cv2.rectangle(img, (cx + 10, Y + 34),
                          (cx + 10 + int(bw * calib_pct), Y + 50),
                          (0, 200, 255), -1)
            self._text(img, f"{int(calib_pct * 100)}%",
                       cx + 10, Y + 65, 0.65, (0, 200, 255), bold=True)

    def render(self, tracker, team_bgr, fps, calibrated,
               n_locked, calib_pct):
        """Rendu complet du dashboard."""
        img = self._make_canvas()
        col1 = team_bgr.get(1, (80, 200, 80))
        col2 = team_bgr.get(2, (80, 80, 200))

        self._draw_header(img, tracker.get_video_elapsed(),
                          fps, calibrated)

        if calibrated:
            self._draw_scoreboard(img, team_bgr, tracker)
            self._draw_possession_section(img, tracker, team_bgr)
            self._draw_chart(img, 20, 435, 390, 118,
                            tracker.hist_time_t1, tracker.hist_time_t2,
                            col1, col2, "HISTORIQUE TEMPS EFFECTIF")
            self._draw_chart(img, 420, 435, 380, 118,
                            tracker.hist_pass_t1, tracker.hist_pass_t2,
                            col1, col2, "HISTORIQUE PASSES")
            self._draw_cards(img, tracker, team_bgr,
                            n_locked, calib_pct)
        else:
            self._rect(img, 20, 100, self.DW - 40,
                       self.DH - 120, self.BG_CARD, radius=12)
            self._text(img, "CALIBRATION EN COURS...",
                       self.DW // 2, 260, 1.0, self.GOLD,
                       bold=True, center=True)
            self._text(img,
                       "Analyse des couleurs de maillots",
                       self.DW // 2, 310, 0.6, self.GRAY, center=True)
            bw = 500
            bx = self.DW // 2 - bw // 2
            by = 360
            cv2.rectangle(img, (bx, by), (bx + bw, by + 30),
                          self.BG_DARK, -1)
            cv2.rectangle(img, (bx, by),
                          (bx + int(bw * calib_pct), by + 30),
                          (0, 200, 255), -1)
            cv2.rectangle(img, (bx, by), (bx + bw, by + 30),
                          self.BORDER, 1)
            self._text(img, f"{int(calib_pct * 100)}%",
                       self.DW // 2, by + 22, 0.7, self.WHITE,
                       bold=True, center=True)

        self._text(img, "Football Analytics v2.0 - Stats corrigées",
                   self.DW - 320, self.DH - 8, 0.36, self.GRAY_DARK)
        return img