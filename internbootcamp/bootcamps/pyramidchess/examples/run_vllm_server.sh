python -m vllm.entrypoints.openai.api_server \
    --model /inspire/hdd/project/multimodal-machine-learning-andcurl http://localhost:8000/v1/models
    --host 0.0.0.0 \
    --port 8000 \
    --trust-remote-code \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.8