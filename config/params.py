"""llama-server 启动参数元数据：标签、提示文案。"""

PARAM_CONFIG = {
    "host": {
        "label": "监听地址 (--host)",
        "tooltip": "服务器绑定的IP地址，0.0.0.0允许所有连接",
    },
    "port": {
        "label": "监听端口 (--port)",
        "tooltip": "服务器监听的端口号，默认8080",
    },
    "ctx_size": {
        "label": "上下文长度 (-c, --ctx-size)",
        "tooltip": "模型处理的上下文最大token数，影响内存占用",
    },
    "threads": {
        "label": "CPU线程数 (-t, --threads)",
        "tooltip": "用于推理的CPU线程数，-1表示自动检测CPU核心数",
    },
    "threads_batch": {
        "label": "批处理线程 (--threads-batch)",
        "tooltip": "用于批处理预计算的CPU线程数，默认与threads相同",
    },
    "n_predict": {
        "label": "最大生成数 (-n, --n-predict)",
        "tooltip": "单次生成的最大token数，-1表示无限制",
    },

    "n_gpu_layers": {
        "label": "GPU加速层数 (-ngl, --n-gpu-layers)",
        "tooltip": "加载到GPU的模型层数，-1表示全部GPU层，999也代表全部",
    },
    "batch_size": {
        "label": "批处理大小 (-b, --batch-size)",
        "tooltip": "预计算批处理的token数，影响内存和速度",
    },
    "ubatch_size": {
        "label": "物理批处理大小 (-ub, --ubatch-size)",
        "tooltip": "物理最大批处理大小，默认512",
    },
    "temp": {
        "label": "温度 (--temp)",
        "tooltip": "采样温度，较低值使输出更确定性，较高值增加创造性",
    },
    "top_k": {
        "label": "Top-K采样 (--top-k)",
        "tooltip": "限制采样候选词数量，数值越小越保守，0表示不限制",
    },
    "top_p": {
        "label": "Top-P采样 (--top-p)",
        "tooltip": "核采样阈值，只选择累积概率超过此值的词",
    },
    "min_p": {
        "label": "最小概率 (--min-p)",
        "tooltip": "最小token概率阈值，过滤掉概率过低的词",
    },
    "presence_penalty": {
        "label": "存在惩罚 (--presence-penalty)",
        "tooltip": "对已出现过的token增加惩罚，避免重复",
    },
    "repeat_penalty": {
        "label": "重复惩罚 (--repeat-penalty)",
        "tooltip": "对重复token的惩罚力度，默认1.0",
    },
    "repeat_last_n": {
        "label": "重复惩罚范围 (--repeat-last-n)",
        "tooltip": "考虑重复的最近token数量",
    },
    "main_gpu": {
        "label": "主GPU编号 (--main-gpu)",
        "tooltip": "当使用多GPU时指定主设备编号",
    },
    "split_mode": {
        "label": "分割模式 (--split-mode)",
        "tooltip": "模型层分割方式：none不分、layer按层、row按行",
    },
    "tensor_split": {
        "label": "张量分割 (--tensor-split)",
        "tooltip": "多GPU间张量分割比例，如0.3,0.7",
    },
    "cpu_moe": {
        "label": "MoE保留CPU (--cpu-moe)",
        "tooltip": "将MoE专家权重全部保留在CPU以节省显存",
    },
    "n_cpu_moe": {
        "label": "MoE保留层数 (--n-cpu-moe)",
        "tooltip": "将MoE专家权重的前N层保留在CPU",
    },
    "spec_type": {
        "label": "投机类型 (--spec-type)",
        "tooltip": "投机解码实现方式：none禁用、draft-simple/eagle3/mtp使用draft模型、ngram-simple/map-k/map-k4v/mod/cache无需draft模型",
    },
    "spec_draft_n_max": {
        "label": "投机token数 (--spec-draft-n-max)",
        "tooltip": "最大draft token数量，0为禁用，默认16",
    },
    "spec_draft_p_min": {
        "label": "投机最小阈值 (--spec-draft-p-min)",
        "tooltip": "draft token被接受的最小概率阈值，范围0~1，默认0.75",
    },
    "n_gpu_layers_draft": {
        "label": "Draft-GPU层数 (--n-gpu-layers-draft)",
        "tooltip": "draft模型加载到GPU的层数，auto自动，0为全部CPU",
    },
    "model_draft": {
        "label": "Draft模型路径 (--model-draft)",
        "tooltip": "投机解码用的draft模型路径（可选）",
    },

    "flash_attn": {
        "label": "Flash注意力 (--flash-attn)",
        "tooltip": "启用Flash Attention加速，可选auto/on/off",
    },
    "mlock": {
        "label": "锁定内存 (--mlock)",
        "tooltip": "将模型锁定在内存中，防止交换到磁盘",
    },
    "cache_type_k": {
        "label": "K缓存类型 (-ctk, --cache-type-k)",
        "tooltip": "Key缓存数据类型",
    },
    "cache_type_v": {
        "label": "V缓存类型 (-ctv, --cache-type-v)",
        "tooltip": "Value缓存数据类型",
    },
    "timeout": {
        "label": "超时 (--timeout)",
        "tooltip": "请求超时时间(秒)",
    },
    "sleep_idle_seconds": {
        "label": "空闲休眠 (--sleep-idle-seconds)",
        "tooltip": "空闲多少秒后进入休眠状态",
    },
    "tools": {
        "label": "工具调用 (--tools)",
        "tooltip": "启用AI智能体的内置工具，如'all'启用所有工具（用于模型调用工具）",
    },
    "seed": {
        "label": "随机种子 (-s, --seed)",
        "tooltip": "随机数种子，-1表示随机",
    },
}
