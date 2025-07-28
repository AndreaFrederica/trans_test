from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from math import radians, degrees, atan2, sqrt
import numpy as np
import cv2
import time
from ursina import invoke
from image_processing import extract_contour_points

# 将像素点映射为方向向量
def spherical_to_direction(pan: float, tilt: float) -> Vec3:
    pr = radians(pan)
    tr = radians(tilt)
    return Vec3(np.cos(tr)*np.sin(pr), np.sin(tr), np.cos(tr)*np.cos(pr))

# 全局状态
screen_width, screen_height = 1.92, 1.08
screen_distance = 5.0
image_w, image_h = 1920, 1080
contour_pixels = extract_contour_points('test_images/test1.png')

pan, tilt = 0.0, 0.0
pan_step, tilt_step = 1.0, 1.0
mode = 'calibrate'
calib_pan_tilt = []  # 存储校准角度
markers = []
homography = None
draw_index = 0
last_draw_time = time.time()

# 初始化应用和场景
app = Ursina()
EditorCamera()  # WASD + 鼠标右键
Text.default_font = 'msyh.ttf'

screen_plane = Entity(model='quad', scale=(screen_width, screen_height, 1),
                      color=color.white, position=(0,0,screen_distance),
                      double_sided=True, collider='box')
gimbal_origin = Entity(model='sphere', scale=0.1, color=color.yellow, position=(0,0,0))
laser = Entity(model=Mesh(vertices=[(0,0,0),(0,0,1)], mode='line'),
               color=color.red, scale=(0.02,0.02,10), position=gimbal_origin.position)

instruction = Text('|←/→ Pan | ↑/↓ Tilt | Enter 记录 | F 重置 |', position=Vec2(0,-0.4), origin=(0,1), background=True, scale=1.2)
pan_text = Text('Pan: 0°', position=Vec2(-0.65,0.4), origin=(0,1))
til_text = Text('Tilt: 0°', position=Vec2(-0.65,0.3), origin=(0,1))
count_text = Text('已记录: 0/4', position=Vec2(-0.65,0.2), origin=(0,1))

screen_x = Slider(min=-3,max=3,default=0,step=0.1,text='屏幕 X',y=0.4,x=0.2)
screen_y = Slider(min=-3,max=3,default=0,step=0.1,text='屏幕 Y',y=0.3,x=0.2)
screen_z = Slider(min=1,max=10,default=screen_distance,step=0.1,text='屏幕 Z',y=0.2,x=0.2)
gimbal_x = Slider(min=-3,max=3,default=0,step=0.1,text='云台 X',y=0.1,x=0.2)
gimbal_y = Slider(min=-3,max=3,default=0,step=0.1,text='云台 Y',y=0.0,x=0.2)
gimbal_z = Slider(min=-1,max=3,default=0,step=0.1,text='云台 Z',y=-0.1,x=0.2)

# 键盘输入事件
def input(key, is_raw=False):
    global pan, tilt, mode, draw_index, homography
    if key == 'left arrow': pan -= pan_step
    if key == 'right arrow': pan += pan_step
    if key == 'up arrow': tilt += tilt_step
    if key == 'down arrow': tilt -= tilt_step
    if mode == 'calibrate' and key in ('enter', 'return'):
        calib_pan_tilt.append((pan, tilt))
        hit = raycast(origin=gimbal_origin.position,
                      direction=spherical_to_direction(pan, tilt), distance=100)
        if hit.entity == screen_plane:
            m = Entity(model='sphere', color=color.azure, scale=0.05, position=hit.point)
            markers.append(m)
        count_text.text = f'已记录: {len(calib_pan_tilt)}/4'
        if len(calib_pan_tilt) == 4:
            src = np.array([[0,1,1],[1,1,1],[1,0,1],[0,0,1]], dtype=np.float32)
            dst = np.array(calib_pan_tilt, dtype=np.float32)
            homography, _ = cv2.findHomography(src, dst)
            mode = 'draw'
    if key == 'f':
        for m in markers: destroy(m)
        calib_pan_tilt.clear(); markers.clear(); homography = None
        draw_index = 0; mode = 'calibrate'; count_text.text='已记录: 0/4'

# 每帧更新
def update():
    global draw_index, pan, tilt, last_draw_time
    screen_plane.position = (screen_x.value, screen_y.value, screen_z.value)
    gimbal_origin.position = (gimbal_x.value, gimbal_y.value, gimbal_z.value)
    laser.position = gimbal_origin.position
    d = spherical_to_direction(pan, tilt)
    pitch = -degrees(atan2(d.y, sqrt(d.x**2 + d.z**2)))
    yaw = degrees(atan2(d.x, d.z))
    laser.rotation = Vec3(pitch, yaw, 0)
    pan_text.text = f'Pan: {pan:.1f}°'
    til_text.text = f'Tilt: {tilt:.1f}°'
    count_text.text = f'已记录: {len(calib_pan_tilt)}/4'
    if mode == 'draw' and homography is not None and draw_index < len(contour_pixels):
        now = time.time()
        if now - last_draw_time >= 0.05:
            u = contour_pixels[draw_index][0] / image_w
            v = 1 - contour_pixels[draw_index][1] / image_h
            pt = np.array([[u,v,1]], dtype=np.float32).T
            mapped = homography @ pt; mapped /= mapped[2]
            pan, tilt = float(mapped[0]), float(mapped[1])
            d2 = spherical_to_direction(pan, tilt)
            hit = raycast(origin=gimbal_origin.position, direction=d2, distance=100)
            if hit.entity == screen_plane:
                glow = Entity(model='quad', texture='circle', color=color.red,
                              scale=0.005, position=hit.point, parent=screen_plane,
                              billboard=True)
                glow.fade_out(duration=30); invoke(destroy, glow, delay=30)
            pitch2 = -degrees(atan2(d2.y, sqrt(d2.x**2 + d2.z**2)))
            yaw2 = degrees(atan2(d2.x, d2.z))
            laser.rotation = Vec3(pitch2, yaw2, 0)
            draw_index += 1
            last_draw_time = now

app.run()
