"""
贪吃蛇 - Python + Pygame
- 蛇身与蛇头颜色不一致
- 蛇头显示眼睛
- 按住空格键加速
- 连续按两下空格键暂停/继续
"""

import pygame
import random
import sys
from typing import List, Tuple

# --- 配置 ---
CELL_SIZE: int = 28
GRID_W: int = 24
GRID_H: int = 18
WIDTH: int = GRID_W * CELL_SIZE
HEIGHT: int = GRID_H * CELL_SIZE
FPS: int = 10
FAST_FPS: int = 20

# 颜色
BG_COLOR        = (24, 28, 32)       # 深色背景
GRID_COLOR      = (34, 38, 42)       # 网格线
FOOD_COLOR      = (255, 85, 85)      # 食物红色
HEAD_COLOR      = (80, 220, 80)      # 蛇头绿色
BODY_COLOR      = (200, 60, 60)      # 蛇身红色
EYE_WHITE_COLOR = (255, 255, 255)    # 眼白
EYE_PUPIL_COLOR = (20, 20, 20)       # 瞳孔
SCORE_COLOR     = (200, 200, 200)    # 分数文字

DIRECTIONS: dict = {
    pygame.K_UP:    (0, -1),
    pygame.K_DOWN:  (0, 1),
    pygame.K_LEFT:  (-1, 0),
    pygame.K_RIGHT: (1, 0),
    pygame.K_w:     (0, -1),
    pygame.K_s:     (0, 1),
    pygame.K_a:     (-1, 0),
    pygame.K_d:     (1, 0),
}


class Snake:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        cx, cy = GRID_W // 2, GRID_H // 2
        self.body: List[Tuple[int, int]] = [
            (cx, cy),
            (cx - 1, cy),
            (cx - 2, cy),
        ]
        self.direction: Tuple[int, int] = (1, 0)
        self.next_direction: Tuple[int, int] = (1, 0)
        self.growing: bool = False

    def head(self) -> Tuple[int, int]:
        return self.body[0]

    def move(self) -> None:
        self.direction = self.next_direction
        hx, hy = self.head()
        dx, dy = self.direction
        new_head = ((hx + dx) % GRID_W, (hy + dy) % GRID_H)

        self.body.insert(0, new_head)
        if self.growing:
            self.growing = False
        else:
            self.body.pop()

    def set_direction(self, dx: int, dy: int) -> None:
        """防止反向"""
        if (dx, dy) == (-self.direction[0], -self.direction[1]):
            return
        self.next_direction = (dx, dy)

    def grow(self) -> None:
        self.growing = True


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("🐍 贪吃蛇 — 空格加速 | 双击空格暂停")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("microsoftyahei,sans-serif", 22, bold=True)
        self.big_font = pygame.font.SysFont("microsoftyahei,sans-serif", 42, bold=True)

        self.snake = Snake()
        self.food: Tuple[int, int] = (0, 0)
        self.score: int = 0
        self.paused: bool = False
        self.game_over: bool = False
        self._last_space_time: int = 0
        self._double_tap_window: int = 300  # ms 内再按一次算双击
        self.spawn_food()

    # ---- 食物 ----
    def spawn_food(self) -> None:
        while True:
            pos = (
                random.randint(0, GRID_W - 1),
                random.randint(0, GRID_H - 1),
            )
            if pos not in self.snake.body:
                self.food = pos
                return

    # ---- 碰撞 ----
    def check_collision(self, pos: Tuple[int, int]) -> bool:
        # 边界穿越：蛇可以穿过墙壁，从左出从右入，从上出从下入
        if pos in self.snake.body[1:]:
            return True
        return False

    # ---- 输入 ----
    def handle_input(self) -> None:
        """处理按键；返回是否消耗了本帧（重置计时器用）。"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # 方向键
                if event.key in DIRECTIONS:
                    self.snake.set_direction(*DIRECTIONS[event.key])

                # 空格：双击检测
                if event.key == pygame.K_SPACE:
                    now = pygame.time.get_ticks()
                    if now - self._last_space_time < self._double_tap_window:
                        # 双击 → 暂停/继续
                        if not self.game_over:
                            self.paused = not self.paused
                        self._last_space_time = 0  # 重置，避免三击
                    else:
                        self._last_space_time = now

                # R 重新开始
                if event.key == pygame.K_r and self.game_over:
                    self.restart()

    # ---- 更新 ----
    def update(self) -> None:
        if self.paused or self.game_over:
            return

        self.snake.move()
        head = self.snake.head()

        if self.check_collision(head):
            self.game_over = True
            return

        if head == self.food:
            self.snake.grow()
            self.score += 10
            self.spawn_food()

    # ---- 绘制 ----
    def draw_grid(self) -> None:
        for x in range(GRID_W):
            for y in range(GRID_H):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)

    def draw_cell(self, pos: Tuple[int, int], color: Tuple[int, int, int]) -> pygame.Rect:
        """绘制一个圆角单元格，返回其 rect。"""
        x, y = pos
        rect = pygame.Rect(
            x * CELL_SIZE + 1, y * CELL_SIZE + 1,
            CELL_SIZE - 2, CELL_SIZE - 2,
        )
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        return rect

    def draw_snake(self) -> None:
        body = self.snake.body

        # 1. 绘制蛇身（不含头）
        for i, segment in enumerate(body):
            if i == 0:
                continue  # 跳过蛇头
            # 越靠近尾部越暗
            ratio = 1.0 - (i / max(len(body) - 1, 1)) * 0.5
            color = (
                int(BODY_COLOR[0] * ratio),
                int(BODY_COLOR[1] * ratio),
                int(BODY_COLOR[2] * ratio),
            )
            self.draw_cell(segment, color)

        # 2. 绘制蛇头
        head = body[0]
        head_rect = self.draw_cell(head, HEAD_COLOR)

        # 3. 绘制眼睛
        self.draw_eyes(head_rect)

    def draw_eyes(self, head_rect: pygame.Rect) -> None:
        """根据蛇的方向在头部绘制两只眼睛。"""
        dx, dy = self.snake.direction
        cx, cy = head_rect.center
        eye_r = CELL_SIZE // 6        # 眼白半径
        pupil_r = max(3, eye_r - 2)   # 瞳孔半径

        # 根据方向计算两只眼睛的基准偏移
        if dx == 1:   # 右
            offsets = [(3, -5), (3, 5)]
            pupil_offsets = [(pupil_r, 0), (pupil_r, 0)]
        elif dx == -1:  # 左
            offsets = [(-3, -5), (-3, 5)]
            pupil_offsets = [(-pupil_r, 0), (-pupil_r, 0)]
        elif dy == -1:  # 上
            offsets = [(-5, -3), (5, -3)]
            pupil_offsets = [(0, -pupil_r), (0, -pupil_r)]
        else:  # 下 (dy == 1)
            offsets = [(-5, 3), (5, 3)]
            pupil_offsets = [(0, pupil_r), (0, pupil_r)]

        for (ox, oy), (px, py) in zip(offsets, pupil_offsets):
            eye_center = (cx + ox, cy + oy)
            pupil_center = (cx + ox + px, cy + oy + py)

            # 眼白
            pygame.draw.circle(self.screen, EYE_WHITE_COLOR, eye_center, eye_r)
            # 瞳孔
            pygame.draw.circle(self.screen, EYE_PUPIL_COLOR, pupil_center, pupil_r)

    def draw_food(self) -> None:
        """带脉冲动画的食物。"""
        rect = self.draw_cell(self.food, FOOD_COLOR)
        # 高光
        highlight = pygame.Rect(rect.x + 4, rect.y + 4, rect.w // 3, rect.h // 3)
        pygame.draw.rect(self.screen, (255, 180, 180), highlight, border_radius=3)

    def draw_ui(self) -> None:
        # 分数
        score_surf = self.font.render(f"分数: {self.score}", True, SCORE_COLOR)
        self.screen.blit(score_surf, (12, 8))

        # 暂停提示
        if self.paused:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            txt = self.big_font.render("已暂停", True, (220, 220, 220))
            self.screen.blit(
                txt, ((WIDTH - txt.get_width()) // 2, (HEIGHT - txt.get_height()) // 2),
            )

        # 游戏结束
        if self.game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            txt1 = self.big_font.render(f"游戏结束  得分: {self.score}", True, (255, 120, 120))
            txt2 = self.font.render("按 R 重新开始", True, SCORE_COLOR)
            self.screen.blit(
                txt1, ((WIDTH - txt1.get_width()) // 2, HEIGHT // 2 - 30),
            )
            self.screen.blit(
                txt2, ((WIDTH - txt2.get_width()) // 2, HEIGHT // 2 + 20),
            )

    # ---- 运行 ----
    def restart(self) -> None:
        self.snake.reset()
        self.spawn_food()
        self.score = 0
        self.paused = False
        self.game_over = False
        self._last_space_time = 0  # 重置双击检测，防止重启后意外暂停

    def run(self) -> None:

        while True:
            self.handle_input()

            # 空格按住 → 加速
            keys = pygame.key.get_pressed()
            fast_mode = keys[pygame.K_SPACE] and not self.paused and not self.game_over

            self.update()

            # 渲染
            self.screen.fill(BG_COLOR)
            self.draw_grid()
            self.draw_food()
            self.draw_snake()
            self.draw_ui()
            pygame.display.flip()

            current_fps = FAST_FPS if fast_mode else FPS
            self.clock.tick(current_fps)


if __name__ == "__main__":
    Game().run()
