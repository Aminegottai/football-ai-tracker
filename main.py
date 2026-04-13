#!/usr/bin/env python3
# ══════════════════════════════════════════════════════
# FOOTBALL ANALYZER - MAIN
# ══════════════════════════════════════════════════════

import cv2
import config
from modules import FootballAnalyzer

def main():
    """Point d'entrée principal."""
    
    # Ouverture vidéo
    cap = cv2.VideoCapture(config.VIDEO_PATH)
    fps_v = cap.get(cv2.CAP_PROP_FPS) or config.DEFAULT_FPS
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"[INFO] Vidéo: {W}x{H} @ {fps_v:.1f}fps")
    print("[INFO] Contrôles: p=pause | r=reset | q=quit")
    print("=" * 50)

    # Initialisation analyseur
    analyzer = FootballAnalyzer(config.MODEL_PATH, fps=fps_v)
    
    # Fenêtres
    cv2.namedWindow('Camera', cv2.WINDOW_NORMAL)
    cv2.namedWindow('Dashboard', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('Camera', config.CAMERA_WIDTH, config.CAMERA_HEIGHT)
    cv2.resizeWindow('Dashboard', config.DASHBOARD_WIDTH, config.DASHBOARD_HEIGHT)
    cv2.moveWindow('Camera', config.CAMERA_X, config.CAMERA_Y)
    cv2.moveWindow('Dashboard', config.DASHBOARD_POS_X, config.DASHBOARD_POS_Y)

    paused = False
    display = None
    dash = None

    # Boucle principale
    while cap.isOpened():
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Traitement
            dets, ball_box = analyzer.process_frame(frame)
            
            # Rendu
            display = analyzer.draw_camera(frame.copy(), dets, ball_box)
            dash = analyzer.get_dashboard()

        # Affichage
        if display is not None:
            cv2.imshow('Camera', display)
        if dash is not None:
            cv2.imshow('Dashboard', dash)

        # Contrôles
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('p'):
            paused = not paused
            print("[PAUSE]" if paused else "[PLAY]")
        elif key == ord('r'):
            analyzer = FootballAnalyzer(config.MODEL_PATH, fps=fps_v)
            print("[RESET]")

    # Fermeture
    cap.release()
    cv2.destroyAllWindows()

    # Statistiques finales
    print("\n" + "=" * 50)
    stats = analyzer.get_stats()
    p1t, p2t = stats['time_possession']
    p1p, p2p = stats['pass_possession']
    t1s, t2s = stats['time_str']
    f1, f2, f0 = stats['frames']
    passes1, passes2 = stats['passes']
    
    print(f"⏱️  POSSESSION TEMPS")
    print(f"   Équipe 1: {p1t}% ({t1s})")
    print(f"   Équipe 2: {p2t}% ({t2s})")
    print(f"\n⚽ PASSES")
    print(f"   Équipe 1: {passes1} passes ({p1p}%)")
    print(f"   Équipe 2: {passes2} passes ({p2p}%)")
    print(f"\n📊 FRAMES")
    print(f"   Équipe 1: {f1} | Équipe 2: {f2} | Libre: {f0}")
    print(f"   Total: {stats['total_frames']} frames ({stats['video_elapsed']:.1f}s)")
    print("=" * 50)


if __name__ == '__main__':
    main()