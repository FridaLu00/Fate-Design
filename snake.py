import pygame
import random
import sys
import threading
from openai import OpenAI
from collections import deque

# --- 核心参数 ---
WIDTH, HEIGHT = 1000, 850
GRID_SIZE = 35   # 增大格子，视觉更清晰
FPS = 5          # 极慢速，确保思考时间

# --- API 配置 ---
SILICONFLOW_API_KEY = "你的_KEY" 
client = OpenAI(
    api_key=SILICONFLOW_API_KEY,
    base_url="https://api.siliconflow.cn/v1",
)

class AISmartSnake:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("AI 语义贪吃蛇 - 操控与视觉重置版")
        self.clock = pygame.time.Clock()
        
        # 字体
        self.font_word = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_ui = pygame.font.SysFont("Microsoft YaHei", 26, bold=True)
        
        # 状态控制
        self.levels = ["小学", "初中", "高中", "大学", "GRE"]
        self.level_idx = 0
        self.word_pool = []
        self.target_word = None
        self.fruits = []
        self.score = 0
        self.wrong_streak = 0
        self.key_buffer = deque(maxlen=2) # 按键缓冲，解决转弯不灵敏
        
        self.init_game()

    def init_game(self):
        """强制等待 AI 第一次加载"""
        self.word_pool = []
        self.fetch_words_sync() # 启动时同步获取一次
        self.reset_snake()
        self.next_question()

    def reset_snake(self):
        # 对齐 GRID_SIZE
        self.snake = [[140, 350], [105, 350], [70, 350]]
        self.direction = "RIGHT"
        self.key_buffer.clear()

    def fetch_words_sync(self):
        """同步获取，确保词库不为空"""
        try:
            prompt = f"提供5个适合{self.levels[self.level_idx]}水平的单词。格式：英文|中文。不要解释。"
            completion = client.chat.completions.create(
                model="Qwen/Qwen2.5-7B-Instruct",
                messages=[{"role": "user", "content": prompt}]
            )
            res = completion.choices[0].message.content.strip()
            for line in res.split('\n'):
                if '|' in line:
                    en, cn = line.split('|')
                    self.word_pool.append({"en": en.strip(), "cn": cn.strip()})
        except Exception as e:
            print(f"AI 加载失败: {e}")
            # 仅在网络彻底断开时使用的保底
            self.word_pool = [{"en": "Network_Error", "cn": "请检查网络"}]

    def next_question(self):
        if len(self.word_pool) < 2:
            # 异步补货，不卡游戏
            threading.Thread(target=self.fetch_words_sync, daemon=True).start()
        
        if self.word_pool:
            self.target_word = self.word_pool.pop(0)
            self.generate_fruits()

    def generate_fruits(self):
        self.fruits = []
        options = [{"text": self.target_word["en"], "correct": True}]
        fakes = ["Object", "System", "Future", "Simple", "Active", "Space"]
        while len(options) < 4:
            f = random.choice(fakes)
            if f not in [o["text"] for o in options]:
                options.append({"text": f, "correct": False})
        
        random.shuffle(options)
        for opt in options:
            while True:
                x = random.randrange(2, (WIDTH-200)//GRID_SIZE) * GRID_SIZE
                y = random.randrange(4, (HEIGHT-80)//GRID_SIZE) * GRID_SIZE
                if [x, y] not in self.snake:
                    w = max(GRID_SIZE, self.font_word.size(opt["text"])[0] + 15)
                    self.fruits.append({"text": opt["text"], "pos": [x, y], "w": w, "ok": opt["correct"]})
                    break

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: self.key_buffer.append("UP")
                if event.key == pygame.K_DOWN: self.key_buffer.append("DOWN")
                if event.key == pygame.K_LEFT: self.key_buffer.append("LEFT")
                if event.key == pygame.K_RIGHT: self.key_buffer.append("RIGHT")

        if self.key_buffer:
            next_dir = self.key_buffer.popleft()
            # 防止原地调头导致自撞
            if next_dir == "UP" and self.direction != "DOWN": self.direction = "UP"
            elif next_dir == "DOWN" and self.direction != "UP": self.direction = "DOWN"
            elif next_dir == "LEFT" and self.direction != "RIGHT": self.direction = "LEFT"
            elif next_dir == "RIGHT" and self.direction != "LEFT": self.direction = "RIGHT"

    def update(self):
        head = list(self.snake[0])
        if self.direction == "UP": head[1] -= GRID_SIZE
        elif self.direction == "DOWN": head[1] += GRID_SIZE
        elif self.direction == "LEFT": head[0] -= GRID_SIZE
        elif self.direction == "RIGHT": head[0] += GRID_SIZE

        if head[0] < 0 or head[0] >= WIDTH or head[1] < 140 or head[1] >= HEIGHT or head in self.snake:
            self.reset_snake(); return

        self.snake.insert(0, head)
        ate = False
        for f in self.fruits:
            rect = pygame.Rect(f["pos"][0], f["pos"][1], f["w"], GRID_SIZE)
            if rect.collidepoint(head[0]+5, head[1]+5): # 碰撞判定微调
                if f["ok"]:
                    self.score += 10
                    self.wrong_streak = 0
                else:
                    self.wrong_streak += 1
                
                # 难度调节
                if self.score > 0 and self.score % 50 == 0:
                    self.level_idx = min(len(self.levels)-1, self.level_idx + 1)
                if self.wrong_streak >= 3:
                    self.level_idx = max(0, self.level_idx - 1)
                    self.wrong_streak = 0
                
                self.next_question()
                ate = True; break
        if not ate: self.snake.pop()

    def draw_scene(self):
        self.screen.fill((10, 10, 15))
        # 强对比网格
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, (30, 30, 40), (x, 140), (x, HEIGHT), 1)
        for y in range(140, HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, (30, 30, 40), (0, y), (WIDTH, y), 1)
        
        # UI
        pygame.draw.rect(self.screen, (40, 45, 60), (0, 0, WIDTH, 140))
        if self.target_word:
            txt = self.font_ui.render(f"请找出翻译为「{self.target_word['cn']}」的单词", True, (255, 215, 0))
            st = self.font_ui.render(f"得分: {self.score}  级别: {self.levels[self.level_idx]}  连错: {self.wrong_streak}/3", True, (255, 255, 255))
            self.screen.blit(txt, (30, 25))
            self.screen.blit(st, (30, 75))

        # 单词
        for f in self.fruits:
            # 单词块背景
            pygame.draw.rect(self.screen, (50, 80, 160), (f["pos"][0], f["pos"][1], f["w"], GRID_SIZE), border_radius=6)
            # 绘制单词
            w_surf = self.font_word.render(f["text"], True, (255, 255, 255))
            self.screen.blit(w_surf, (f["pos"][0]+8, f["pos"][1]+5))

        # 蛇
        for i, p in enumerate(self.snake):
            color = (0, 255, 127) if i == 0 else (0, 200, 100)
            pygame.draw.rect(self.screen, color, (p[0]+2, p[1]+2, GRID_SIZE-4, GRID_SIZE-4), border_radius=4)

    def run(self):
        while True:
            self.handle_input()
            self.update()
            self.draw_scene()
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    AISmartSnake().run()