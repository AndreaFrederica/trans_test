"""
Module to compute true mapping and homography for calibration.
"""
import numpy as np
import cv2

def true_mapping(x: float, y: float,
                 screen_w: int, screen_h: int,
                 pan_range: tuple[float,float],
                 tilt_range: tuple[float,float]) -> tuple[float,float]:
    """
    Simulated "true" mapping from image pixel (x,y) to gimbal angles (pan, tilt).
    pan linear maps x to pan_range, tilt maps (h-y) to tilt_range.
    """
    pan_min, pan_max = pan_range
    tilt_min, tilt_max = tilt_range
    pan = pan_min + (x / screen_w) * (pan_max - pan_min)
    tilt = tilt_min + ((screen_h - y) / screen_h) * (tilt_max - tilt_min)
    return pan, tilt


def compute_homography(img_pts: list[tuple[float,float]],
                       pan_tilt_pts: list[tuple[float,float]]) -> np.ndarray:
    """
    Given corresponding image and gimbal points, compute homography matrix H
    such that [pan, tilt, 1].T ~ H * [x, y, 1].T
    """
    src = np.array(img_pts, dtype=np.float32)
    dst = np.array(pan_tilt_pts, dtype=np.float32)
    H, _ = cv2.findHomography(src, dst)
    return H