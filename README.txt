# AI Smart Snake (AI 语义贪吃蛇)

这是一个结合了 **Python Pygame** 和 **SiliconFlow (Qwen2.5)** 大模型的创新学习游戏。

### 核心特性
- 🐍 **AI 驱动**：单词果实由大模型实时生成，而非本地预设。
- 📈 **动态难度**：AI 会根据你的游戏表现（连错或连对）自动切换词库等级（小学 -> GRE）。
- ⌨️ **优化体验**：支持指令缓冲、自适应单词宽度以及极简慢速操控。

### 如何运行
1. 安装依赖：`pip install pygame-ce openai`
2. 在 `snake.py` 中填入你的 SiliconFlow API Key。
3. 运行：`python snake.py`