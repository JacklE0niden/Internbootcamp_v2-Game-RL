import random
from typing import Dict, Any, Optional

from internbootcamp.src.base_instruction_generator import BaseInstructionGenerator

# 导入 PyramidChess 数据生成模块（现在在同一个目录下）
from . import pyramidchess_data_generate as pc_data_gen
from . import pyramidchess_board_generate as pc_board_gen
from . import pyramidchess_image_generate as pc_image_gen


class PyramidChessInstructionGenerator(BaseInstructionGenerator):
    """PyramidChess 指令生成器，用于生成 PyramidChess 游戏的训练数据"""
    
    def __init__(self, 
                 question_id_list: Optional[list[int]] = None,
                 plot_level_list: Optional[list[str]] = None,
                 param_list: Optional[list] = None,
                 example: bool = False,
                 max_turn: Optional[int] = None,
                 seed: Optional[int] = None,
                 **kwargs):
        """
        初始化 PyramidChess 指令生成器
        
        Args:
            question_id_list: 问题类型ID列表，支持 0-5
            plot_level_list: 难度级别列表，支持 "Easy", "Medium", "Hard"
            param_list: 参数列表，用于特定问题类型
            example: 是否生成示例数据
            max_turn: 最大回合数
            seed: 随机种子
        """
        super().__init__()
        self.question_id_list: list[int] = question_id_list or [0, 1, 2, 3, 4, 5]
        self.plot_level_list: list[str] = plot_level_list or ["Easy", "Medium", "Hard"]
        self.param_list: list = param_list or [0.25]  # 默认参数
        self.example: bool = example
        self.max_turn: Optional[int] = max_turn
        self.seed: Optional[int] = seed
        
        if self.seed is not None:
            random.seed(self.seed)
        
        # 确保数据目录结构存在
        pc_data_gen.check_file_structure(example=self.example)
        
        # 用于跟踪生成的案例ID
        self.case_counter: int = 0
    
    def case_generator(self) -> Dict[str, Any]:
        """
        生成单个 PyramidChess 任务案例
        
        Returns:
            Dict[str, Any]: 包含任务信息的字典
        """
        if self.seed is not None:
            random.seed(self.seed + self.case_counter)
        
        # 随机选择问题类型和难度级别
        question_id = random.choice(self.question_id_list)
        plot_level = random.choice(self.plot_level_list)
        
        # 获取问题信息
        question_type, qa_type, qa_level, question_description = pc_data_gen.get_question_info(question_id)
        
        # 生成游戏棋盘
        if question_id == 3:
            # 问题类型3需要特殊处理
            board, take_point, turn, take_pos = pc_board_gen.board_generate_stop_at_take(plot_level=plot_level)
            param_list = [take_point, turn, take_pos]
        else:
            board = pc_board_gen.board_generate(max_turn=self.max_turn, plot_level=plot_level)
            param_list = self.param_list
        
        # 获取棋盘状态
        layers = board.board_dict()
        
        # 生成图像
        data_id = f"pyramidchess-{question_type}-{str(self.case_counter).zfill(5)}-{qa_type}"
        image_id = self.case_counter
        
        # 生成图像
        # 注意：combine_image_generate 会在当前工作目录的 pyramidchess_dataset/images/ 下保存图像
        # 图像路径相对于数据集目录
        base_dir = "pyramidchess_dataset_example" if self.example else "pyramidchess_dataset"
        image_path = f"{base_dir}/images/board_{str(image_id).zfill(5)}.png"
        pc_image_gen.combine_image_generate(
            id=image_id, 
            layers=layers, 
            example=self.example, 
            plot_level=plot_level
        )
        
        # 生成问题和答案
        question, answer, analysis, options = pc_data_gen.question_generate(
            question_id, board, param_list=param_list
        )
        
        # 构建 identity 字典
        identity = {
            "data_id": data_id,
            "question_id": question_id,
            "question_type": question_type,
            "qa_type": qa_type,
            "qa_level": qa_level,
            "question_description": question_description,
            "plot_level": plot_level,
            "question": question,
            "answer": answer,
            "analysis": analysis,
            "options": options,
            "image_path": image_path,
            "state": layers,  # 保存完整状态
            "board_size": len(board.Board)  # 棋盘大小
        }
        
        self.case_counter += 1
        
        return identity
    
    def prompt_func(self, identity: Dict[str, Any]) -> Any:
        """
        根据任务信息生成提示语
        
        Args:
            identity (Dict[str, Any]): 任务信息
            
        Returns:
            Any: 生成的提示语（对于多模态任务，返回包含文本和图像的字典；对于纯文本任务，返回字符串）
        """
        question = identity.get("question", "")
        question_type = identity.get("question_type", "")
        
        # 对于多模态任务，返回包含文本和图像的字典
        # 注意：必须包含 'question' 键，因为 data_generation.py 需要它
        if question_type == "mcq":
            # MCQ 类型问题
            prompt: Dict[str, Any] = {
                "prompt_txt": question,
                "prompt_img": identity.get("image_path", ""),
                "question": question,  # 添加 question 键供 data_generation.py 使用
                "options": identity.get("options", [])
            }
        else:
            # Fill 类型问题
            prompt: Dict[str, Any] = {
                "prompt_txt": question,
                "prompt_img": identity.get("image_path", ""),
                "question": question  # 添加 question 键供 data_generation.py 使用
            }
        
        return prompt

