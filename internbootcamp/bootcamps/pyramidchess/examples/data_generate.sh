#!/bin/bash
# PyramidChess 数据生成示例脚本

# 生成训练和测试数据
python -m internbootcamp.utils.data_generation \
    --instruction-config internbootcamp/bootcamps/pyramidchess/configs/pyramidchess_instruction_config.yaml \
    --output-dir data/pyramidchess \
    --split-samples "train:10000,test:1000" \
    --shuffle