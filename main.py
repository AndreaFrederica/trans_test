from ursina import *
from ursina.prefabs.editor_camera import EditorCamera
from math import radians, degrees, atan2, sqrt
import numpy as np
from ursina import invoke
# 加载轮廓提取模块
from image_processing import extract_contour_points

# 初始化应用
app = Ursina()
# 原生 3D 相机控制
editor_camera = EditorCamera()
# 中文字体支持，请确保当前目录下有 msyh.ttf
Text.default_font = 'msyh.ttf'

# 参数
screen_width, screen_height = 1.92, 1.08
screen_distance = 5.0
# 对应的图像像素尺寸
image_w, image_h = 1920, 1080
# 提取并加载轮廓像素点
contour_pixels = extract_contour_points('test_images/test1.png')

# 云台视角参数
pan, tilt = 0.0, 0.0
pan_step, tilt_step = 1.0, 1.0

# 模式和状态
mode = 'calibrate'  # 'calibrate' 或 'draw'
calib_points: list[Vec3] = []
markers: list[Entity] = []
draw_index = 0

# 场景实体
# 给平面添加碰撞器
screen_plane = Entity(
    model='quad',
    scale=(screen_width, screen_height, 1),
    color=color.white,
    position=(0, 0, screen_distance),
    double_sided=True,
    collider='box'
)
# 云台原点
gimbal_origin = Entity(
    model='sphere',
    scale=0.1,
    color=color.yellow,
    position=(0, 0, 0)
)

# 激光射线
laser = Entity(
    model=Mesh(vertices=[(0,0,0),(0,0,1)], mode='line'),
    color=color.red,
    scale=(0.02,0.02,10),
    position=gimbal_origin.position
)

# UI 元素
# 文本提示（左上角）
instruction = Text(
    '|←/→ Pan | ↑/↓ Tilt | Enter 记录 | F 重置 |',
    position=Vec2(0,-0.4), origin=(0,1), background=True, scale=1.2
)
pan_text = Text(
    text=f'Pan: {pan:.1f}°',
    position=Vec2(-0.65, 0.4), origin=(0,1), scale=1.1
)
til_text = Text(
    text=f'Tilt: {tilt:.1f}°',
    position=Vec2(-0.65, 0.3), origin=(0,1), scale=1.1
)
count_text = Text(
    text=f'已记录: {len(calib_points)}/4',
    position=Vec2(-0.65, 0.2), origin=(0,1), scale=1.1
)
# 滑块定义（屏幕底部）
screen_x = Slider(min=-3, max=3, default=0, step=0.1, text='屏幕 X', y=0.4)
screen_y = Slider(min=-3, max=3, default=0, step=0.1, text='屏幕 Y', y=0.3)
screen_z = Slider(min=1, max=10, default=screen_distance, step=0.1, text='屏幕 Z', y=0.2)

gimbal_x = Slider(min=-3, max=3, default=0, step=0.1, text='云台 X', y=0.1)
gimbal_y = Slider(min=-3, max=3, default=0, step=0.1, text='云台 Y', y=0)
gimbal_z = Slider(min=-1, max=3, default=0, step=0.1, text='云台 Z', y=-0.1)

# 工具函数
def spherical_to_direction(p, t):
    pr, tr = radians(p), radians(t)
    return Vec3(np.cos(tr)*np.sin(pr), np.sin(tr), np.cos(tr)*np.cos(pr))

# 输入回调
def input(key):
    print(f"Pressed key: {key}")  # Debug按键事件
    global pan, tilt, mode, draw_index, calib_points
    global pan, tilt, mode, draw_index, calib_points
    if key == 'left arrow': pan -= pan_step
    if key == 'right arrow': pan += pan_step
    if key == 'up arrow': tilt += tilt_step
    if key == 'down arrow': tilt -= tilt_step
    if key in ('enter', 'return') and mode == 'calibrate':
        hit = raycast(
            origin=gimbal_origin.position,
            direction=spherical_to_direction(pan, tilt),
            distance=50
        )
        if hit.entity == screen_plane:
            calib_points.append(hit.point)
            m = Entity(model='sphere', color=color.azure, scale=0.05, position=hit.point)
            markers.append(m)
            count_text.text = f'已记录: {len(calib_points)}/4'
        if len(calib_points) == 4:
            mode = 'draw'
    if key == 'f' and mode == 'draw':
        draw_index = 0
        # 清除校准点标记
        for m in markers:
            destroy(m)
        markers.clear()
        calib_points.clear()
        count_text.text = '已记录: 0/4'
        mode = 'calibrate'

# 每帧更新
def update():
    global draw_index
    # 更新屏幕和云台位置
    screen_plane.position = (screen_x.value, screen_y.value, screen_z.value)
    gimbal_origin.position = (gimbal_x.value, gimbal_y.value, gimbal_z.value)
    laser.position = gimbal_origin.position
    # 更新激光方向
    d = spherical_to_direction(pan, tilt)
    pitch = -degrees(atan2(d.y, sqrt(d.x**2 + d.z**2)))
    yaw = degrees(atan2(d.x, d.z))
    laser.rotation = Vec3(pitch, yaw, 0)
    # 更新 UI 文本
    pan_text.text = f'Pan: {pan:.1f}°'
    til_text.text = f'Tilt: {tilt:.1f}°'
    count_text.text = f'已记录: {len(calib_points)}/4'
    # 绘制模式：模拟激光在屏幕上的余晖
    if mode == 'draw' and draw_index < len(contour_pixels):
        ix, iy = contour_pixels[draw_index]
        u = (ix / image_w - 0.5) * screen_width
        v = (0.5 - iy / image_h) * screen_height
        world_pt = screen_plane.position + Vec3(u, v, 0)
        glow = Entity(
            model='quad', texture='circle', color=color.red,
            scale=0.02, position=world_pt, parent=screen_plane,
            billboard=True
        )
        glow.animate_scale(Vec3(0.1,0.1,0.1), duration=0.3)
        invoke(destroy, glow, delay=0.5)
        draw_index += 1

app.run()
