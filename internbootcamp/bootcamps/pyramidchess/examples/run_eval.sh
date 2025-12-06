#!/bin/bash
# PyramidChess 评估脚本

DATASET_PATH=$(ls -t data/pyramidchess/pyramidchess_*_test.jsonl 2>/dev/null | head -1)

if [ -z "$DATASET_PATH" ]; then
    echo "错误: 未找到测试数据集文件"
    echo "请确保已运行数据生成脚本，或手动指定 --dataset-path 参数"
    exit 1
fi

echo "使用数据集: $DATASET_PATH"

python -m internbootcamp.utils.run_evaluation \
  --dataset-path "$DATASET_PATH" \
  --output-dir outputs/pyramidchess/ \
  --api-key "null" \
  --api-url "http://100.102.196.26:30001/v1" \
  --api-model "Qwen/Qwen3VL-8B-Instruct" \
  --reward-calculator-class "internbootcamp.bootcamps.pyramidchess.pyramidchess_reward_calculator.PyramidChessRewardCalculator"

