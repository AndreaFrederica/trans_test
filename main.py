"""
Main pygame application: calibration UI and simulation animation.
"""
import sys
import pygame
import numpy as np
from calibrator import true_mapping, compute_homography
from image_processing import extract_contour_points

# Configuration
default_screen_w, default_screen_h = 1920, 1080
pan_range = (0.0, 180.0)
tilt_range = (0.0, 90.0)

# Pygame window size
WIN_W, WIN_H = 1200, 600
SCREEN_VIEW = pygame.Rect(0, 0, WIN_W // 2, WIN_H)
GIMBAL_VIEW = pygame.Rect(WIN_W // 2, 0, WIN_W // 2, WIN_H)

# Load image and extract contours
IMAGE_PATH = 'test_images/test1.png'
contour_pts = extract_contour_points(IMAGE_PATH)

# States
calib_clicks = []  # store screen clicks
pan_tilt_calib = []
H = None
mode = 'calibrate'

pygame.init()
screen = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption('Gimbal-Laser Simulation')
font = pygame.font.SysFont(None, 24)

# Load & scale image to screen view
# Convert to 32-bit surface before smoothscale to avoid ValueError
orig_img = pygame.image.load(IMAGE_PATH).convert_alpha()
img_w, img_h = orig_img.get_size()
scale = min(SCREEN_VIEW.w / img_w, SCREEN_VIEW.h / img_h)
img_surf = pygame.transform.smoothscale(orig_img, (int(img_w*scale), int(img_h*scale)))
img_rect = img_surf.get_rect(center=SCREEN_VIEW.center)

clock = pygame.time.Clock()
idx = 0

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and mode == 'calibrate':
            mx, my = event.pos
            if SCREEN_VIEW.collidepoint(mx, my):
                # map to image pixel coords
                ix = (mx - img_rect.x) / scale
                iy = (my - img_rect.y) / scale
                calib_clicks.append((ix, iy))
                # simulate true pan/tilt
                pan, tilt = true_mapping(ix, iy,
                                          default_screen_w, default_screen_h,
                                          pan_range, tilt_range)
                pan_tilt_calib.append((pan, tilt))
                if len(calib_clicks) == 4:
                    H = compute_homography(calib_clicks, pan_tilt_calib)
                    mode = 'draw'
    # Draw background
    screen.fill((30,30,30))
    # Draw screen view
    screen.fill((50,50,50), SCREEN_VIEW)
    screen.blit(img_surf, img_rect)
    # Draw calibration markers
    if mode == 'calibrate':
        for i, (ix, iy) in enumerate(calib_clicks):
            px = int(ix*scale + img_rect.x)
            py = int(iy*scale + img_rect.y)
            pygame.draw.circle(screen, (255,0,0), (px,py), 5)
            txt = font.render(str(i+1), True, (255,255,255))
            screen.blit(txt, (px+5,py+5))
        prompt = font.render('Click 4 corners: TL,TR,BR,BL', True, (200,200,200))
        screen.blit(prompt, (10,10))
    # Draw simulation
    if mode == 'draw' and H is not None:
        # draw gimbal view border
        screen.fill((40,40,40), GIMBAL_VIEW)
        # Compute and animate path
        if idx < len(contour_pts):
            pt = contour_pts[idx]
            v = np.array([[pt[0], pt[1],1.0]], dtype=np.float32).T
            out = H @ v
            out /= out[2]
            pan, tilt = out[0][0], out[1][0]
            # map pan/tilt to view coords
            gx = GIMBAL_VIEW.x + (pan - pan_range[0]) / (pan_range[1]-pan_range[0]) * GIMBAL_VIEW.w
            gy = GIMBAL_VIEW.y + (GIMBAL_VIEW.h - (tilt - tilt_range[0]) / (tilt_range[1]-tilt_range[0]) * GIMBAL_VIEW.h)
            # draw point
            pygame.draw.circle(screen, (0,255,0), (int(gx),int(gy)), 3)
            idx += 1
        prompt2 = font.render('Drawing contour (green) on gimbal view', True, (200,200,200))
        screen.blit(prompt2, (GIMBAL_VIEW.x+10,10))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()