import re
import json
import ast
from typing import Optional, Dict, Any
from internbootcamp.src.base_reward_calculator import BaseRewardCalculator


class PyramidChessRewardCalculator(BaseRewardCalculator):
    """PyramidChess 奖励计算器，用于评估模型输出"""
    
    @staticmethod
    def extract_output(output_str: str) -> Optional[Dict[str, Any]]:
        """
        从模型输出中提取答案
        
        Args:
            output_str (str): 模型的原始输出
            
        Returns:
            Optional[Dict[str, Any]]: 提取的答案信息，包含答案类型和值
        """
        if not output_str:
            return None
        
        output_str = output_str.strip()
        
        # 尝试提取JSON格式的答案
        json_pattern = r'\{[^{}]*"answer"[^{}]*\}'
        json_matches = re.finditer(json_pattern, output_str, re.DOTALL)
        for match in json_matches:
            try:
                result = json.loads(match.group())
                if "answer" in result:
                    return {"type": "json", "value": result["answer"]}
            except:
                continue
        
        # 尝试提取数字答案（用于fill类型问题）
        # 匹配 "X" 或 "X step(s)" 或 "There are X balls" 等格式
        number_patterns = [
            r'(\d+)\s*step[s]?',  # "12 steps" 或 "12 step"
            r'(\d+)\s*ball[s]?',   # "13 balls" 或 "13 ball"
            r'There are (\d+)',    # "There are 13"
            r'(\d+)',              # 纯数字
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, output_str, re.IGNORECASE)
            if matches:
                try:
                    return {"type": "number", "value": int(matches[-1])}
                except:
                    continue
        
        # 尝试提取坐标答案（用于问题类型3）
        # 匹配 "[x, y] at level z" 或 "(x, y) at level z" 格式
        coord_patterns = [
            r'\[(\d+),\s*(\d+)\]\s*at\s*level\s*(\d+)',
            r'\((\d+),\s*(\d+)\)\s*at\s*level\s*(\d+)',
            r'(\d+),\s*(\d+)\s*at\s*level\s*(\d+)',
        ]
        
        for pattern in coord_patterns:
            match = re.search(pattern, output_str, re.IGNORECASE)
            if match:
                try:
                    x, y, level = map(int, match.groups())
                    return {"type": "coordinate", "value": {"position": [x, y], "level": level}}
                except:
                    continue
        
        # 尝试提取选项编号（用于MCQ类型问题）
        # 匹配 "1", "2", "3", "4" 等选项编号
        option_patterns = [
            r'\b([1-5])\b',  # 单个数字1-5
            r'Option\s*([1-5])',  # "Option 1"
            r'Answer:\s*([1-5])',  # "Answer: 1"
        ]
        
        for pattern in option_patterns:
            matches = re.findall(pattern, output_str, re.IGNORECASE)
            if matches:
                try:
                    return {"type": "option", "value": int(matches[-1])}
                except:
                    continue
        
        # 尝试提取选项文本（用于MCQ类型问题）
        # 匹配选项文本内容
        option_texts = [
            "PLAYER_0", "PLAYER_1", "Empty", "Index out of bound",
            "Can place and no balls taken",
            "Can place and then balls can be taken",
            "Cannot place, position already occupied",
            "Cannot place, ball not ready below",
            "The coordinate is out of bound",
            "It contain a ball and the ball can't be taken",
            "It contain a ball and can be taken",
            "It doesn't contain a ball and a ball can't be put here",
            "It doesn't contain a ball and a ball can be put here",
            "It doesn't contain a ball and the player can put a ball here this turn",
            "It doesn't contain a ball and the player can't put a ball here this turn",
        ]
        
        for option_text in option_texts:
            if option_text.lower() in output_str.lower():
                return {"type": "option_text", "value": option_text}
        
        return None
    
    @classmethod
    def _verify_correction(cls, extracted_output, identity: dict, **kwargs) -> float:
        """
        验证用户输出并计算得分
        
        Args:
            extracted_output: 提取的答案信息
            identity (dict): 任务信息，包含期望的答案
            **kwargs: 其他参数
            
        Returns:
            float: 得分 (0.0 到 1.0)
        """
        try:
            if not extracted_output:
                return 0.0
            
            expected_answer = identity.get("answer")
            question_id = identity.get("question_id")
            question_type = identity.get("question_type")
            
            if expected_answer is None:
                return 0.0
            
            # 根据问题类型进行不同的验证
            if question_type == "mcq":
                # MCQ类型：答案应该是选项编号（1-5）
                if isinstance(expected_answer, int):
                    # 期望答案是数字
                    if extracted_output.get("type") == "option":
                        extracted_value = extracted_output.get("value")
                        if extracted_value == expected_answer:
                            return 1.0
                        else:
                            return 0.0
                    elif extracted_output.get("type") == "option_text":
                        # 如果提取的是文本，需要映射回选项编号
                        options = identity.get("options", [])
                        extracted_text = extracted_output.get("value")
                        try:
                            extracted_index = options.index(extracted_text) + 1
                            if extracted_index == expected_answer:
                                return 1.0
                            else:
                                return 0.0
                        except ValueError:
                            return 0.0
                    else:
                        return 0.0
                else:
                    return 0.0
            
            elif question_type == "fill":
                # Fill类型：答案可能是数字或坐标
                if question_id == 2:
                    # 问题类型2：需要数字答案（步数）
                    if isinstance(expected_answer, (int, str)):
                        expected_num = int(str(expected_answer).strip())
                        if extracted_output.get("type") == "number":
                            extracted_value = extracted_output.get("value")
                            if extracted_value == expected_num:
                                return 1.0
                            else:
                                # 允许一定的误差范围
                                diff = abs(extracted_value - expected_num)
                                if diff == 0:
                                    return 1.0
                                elif diff <= 1:
                                    return 0.5  # 部分正确
                                else:
                                    return 0.0
                        else:
                            return 0.0
                    else:
                        return 0.0
                
                elif question_id == 3:
                    # 问题类型3：需要坐标答案 "[x, y] at level z"
                    if isinstance(expected_answer, str):
                        # 解析期望答案 "x, y at level z" 或 "[x, y] at level z"
                        expected_match = re.search(r'\[?(\d+),\s*(\d+)\]?\s*at\s*level\s*(\d+)', expected_answer)
                        if expected_match:
                            expected_pos = [int(expected_match.group(1)), int(expected_match.group(2))]
                            expected_level = int(expected_match.group(3))
                            
                            if extracted_output.get("type") == "coordinate":
                                extracted_value = extracted_output.get("value")
                                extracted_pos = extracted_value.get("position")
                                extracted_level = extracted_value.get("level")
                                
                                if (extracted_pos == expected_pos and 
                                    extracted_level == expected_level):
                                    return 1.0
                                else:
                                    return 0.0
                            else:
                                return 0.0
                        else:
                            return 0.0
                    else:
                        return 0.0
                
                elif question_id == 4:
                    # 问题类型4：需要数字答案（球的数量）
                    if isinstance(expected_answer, (int, str)):
                        expected_num = int(str(expected_answer).strip())
                        if extracted_output.get("type") == "number":
                            extracted_value = extracted_output.get("value")
                            if extracted_value == expected_num:
                                return 1.0
                            else:
                                return 0.0
                        else:
                            return 0.0
                    else:
                        return 0.0
                
                else:
                    # 其他fill类型问题
                    if isinstance(expected_answer, str):
                        # 字符串匹配（忽略大小写和空格）
                        expected_clean = expected_answer.strip().lower()
                        if extracted_output.get("type") == "option_text":
                            extracted_clean = extracted_output.get("value", "").strip().lower()
                            if extracted_clean == expected_clean:
                                return 1.0
                            else:
                                return 0.0
                        else:
                            return 0.0
                    else:
                        return 0.0
            
            else:
                return 0.0
            
        except Exception as e:
            print(f"[DEBUG PyramidChessRewardCalculator] 验证时出错: {str(e)}")
            import traceback
            print(f"[DEBUG PyramidChessRewardCalculator] 异常堆栈:\n{traceback.format_exc()}")
            return 0.0

