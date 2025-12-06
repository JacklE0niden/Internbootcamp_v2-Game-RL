# PyramidChess Bootcamp

PyramidChess 是一个3D策略游戏，本 bootcamp 实现了在 InternBootcamp_v2 框架中集成 PyramidChess 游戏，用于生成训练数据和评估模型性能。

## 游戏规则

PyramidChess 是一个基于3D金字塔结构的策略游戏：
- 游戏棋盘是方形的，有3x3、4x4或5x5三种尺寸
- 棋盘分为多个层级（Level 0 到 Level n-1）
- 两个玩家轮流放置球（PLAYER_0 使用蓝色球，PLAYER_1 使用红色球）
- 球只能放置在已有完整2x2基础的位置上
- 当玩家完成同色的2x2方块时，可以取回最多2个球
- 最先在金字塔顶部放置球的玩家获胜

## 支持的问题类型

本 bootcamp 支持6种问题类型（question_id: 0-5）：

1. **TargetPerception (question_id: 0, 4, 5)**
   - 问题0: 询问指定坐标的球的状态（PLAYER_0/PLAYER_1/Empty/Index out of bound）
   - 问题4: 计算棋盘上球的总数
   - 问题5: 询问坐标的高级状态（是否合法、是否有球、球是否可取、是否可以放置）

2. **StatePrediction (question_id: 1, 2)**
   - 问题1: 判断指定坐标是否可以放置球，以及放置后的结果
   - 问题2: 计算在指定坐标放置球需要多少步

3. **StrategyOptimization (question_id: 3)**
   - 问题3: 给出在当前局面下的最佳放置位置

## 文件结构

```
pyramidchess/
├── __init__.py
├── pyramidchess_instruction_generator.py  # 指令生成器
├── pyramidchess_reward_calculator.py      # 奖励计算器
├── configs/
│   └── pyramidchess_instruction_config.yaml  # 配置文件
└── README.md
```

## 使用方法

### 1. 生成训练数据

使用配置文件生成数据：

```bash
python -m internbootcamp.utils.data_generation \
    --instruction-config internbootcamp/bootcamps/pyramidchess/configs/pyramidchess_instruction_config.yaml \
    --output-dir data/pyramidchess \
    --split-samples "train:10000,test:1000"
```

### 2. 配置说明

配置文件 `pyramidchess_instruction_config.yaml` 包含多个生成器配置：

- **easy_target_perception**: 生成简单级别的目标感知问题
- **medium_state_prediction**: 生成中等难度的状态预测问题
- **hard_strategy_optimization**: 生成困难级别的策略优化问题
- **mixed_all_levels**: 混合所有类型和难度的问题

每个配置可以自定义：
- `question_id_list`: 问题类型列表
- `plot_level_list`: 难度级别列表（Easy/Medium/Hard）
- `generation_ratio`: 生成比例

### 3. 评估模型

在评估配置中使用 PyramidChess 的 reward calculator：

```python
from internbootcamp.bootcamps.pyramidchess.pyramidchess_reward_calculator import PyramidChessRewardCalculator

reward_calculator = PyramidChessRewardCalculator()
```

## 数据格式

生成的数据包含以下字段：

- `data_id`: 数据唯一标识符
- `question_id`: 问题类型ID (0-5)
- `question_type`: 问题类型（"mcq" 或 "fill"）
- `qa_type`: QA类型（"TargetPerception", "StatePrediction", "StrategyOptimization"）
- `qa_level`: 难度级别（"Easy", "Medium", "Hard"）
- `question`: 问题文本（包含游戏规则）
- `answer`: 正确答案
- `analysis`: 答案分析
- `options`: 选项列表（仅MCQ类型）
- `image_path`: 游戏状态图像路径
- `state`: 游戏状态（JSON格式）

## 注意事项

1. **依赖项**: 需要确保 `Game-RL/src/PyramidChess` 目录存在且包含必要的模块：
   - `pyramidchess_data_generate.py`
   - `pyramidchess_board_generate.py`
   - `pyramidchess_image_generate.py`

2. **图像路径**: 生成的图像会保存在 `pyramidchess_dataset/images/` 目录下，确保该目录存在。

3. **状态文件**: 游戏状态会保存在 `pyramidchess_dataset/states/` 目录下。

4. **多模态支持**: 本 bootcamp 支持多模态输入（文本+图像），prompt 返回格式为字典：
   ```python
   {
       "prompt_txt": "问题文本",
       "prompt_img": "图像路径",
       "options": [...]  # 仅MCQ类型
   }
   ```

## 验证函数说明

`PyramidChessRewardCalculator` 实现了以下验证逻辑：

1. **MCQ类型问题**: 验证模型输出的选项编号或选项文本是否与正确答案匹配
2. **Fill类型问题**:
   - 问题2: 验证数字答案（步数）
   - 问题3: 验证坐标答案格式 "[x, y] at level z"
   - 问题4: 验证数字答案（球的数量）

验证函数会从模型输出中提取答案，支持多种格式：
- JSON格式: `{"answer": ...}`
- 数字格式: "12 steps", "13 balls"
- 坐标格式: "[x, y] at level z"
- 选项编号: "1", "2", "3", "4"
- 选项文本: "PLAYER_0", "Empty" 等

## 示例

生成包含所有问题类型和难度级别的数据：

```bash
python -m internbootcamp.utils.data_generation \
    --instruction-config internbootcamp/bootcamps/pyramidchess/configs/pyramidchess_instruction_config.yaml \
    --output-dir data/pyramidchess \
    --split-samples "train:5000,test:500" \
    --shuffle
```

生成特定类型的问题：

修改配置文件，只启用 `easy_target_perception` 配置，并设置 `generation_ratio: 1`。

