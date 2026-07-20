# 完整跑通示例：S4 论文摘要压缩

## 第 1 步：生成骨架

```bash
python scripts/init_skeleton.py --out summary.json
```

## 第 2 步：读摘要后整理出的 values.json

```json
{
  "why": {
    "task": "长序列建模（如长文本、时间序列、音频）",
    "methods": "RNN、CNN、Transformer 自注意力",
    "capability": "长距离依赖捕捉",
    "scenario": "序列长度达到数千甚至上万步"
  },
  "how": {
    "method_name": "S4（结构化状态空间序列模型）",
    "mechanism": "对角加低秩（DPLR）参数化的状态空间模型，并结合 HiPPO 矩阵初始化",
    "capability_achieved": "高效建模任意长度序列中的长程依赖",
    "effect": "将计算复杂度降低到接近线性，同时大幅提升长序列任务上的建模能力"
  },
  "so_what": {
    "benchmark": "Long Range Arena 等长序列基准",
    "improvement": "多项长序列任务上的最优表现，并首次解决了 16k 长度的 Path-X 任务"
  }
}
```

```bash
python scripts/fill_summary.py --skeleton summary.json --values values.json --out summary_filled.json
```

## 第 3 步：渲染 + 判定自检

```bash
python scripts/render_summary.py --in summary_filled.json
```

输出三句话：

> 在长序列建模（如长文本、时间序列、音频）任务中，现有方法（RNN、CNN、Transformer 自注意力）在长距离依赖捕捉关键能力上仍存在不足，尤其是在序列长度达到数千甚至上万步场景下表现受限。
>
> 为了解决这一问题，本文提出S4（结构化状态空间序列模型），其核心是通过对角加低秩（DPLR）参数化的状态空间模型，并结合 HiPPO 矩阵初始化来实现高效建模任意长度序列中的长程依赖能力，从而将计算复杂度降低到接近线性，同时大幅提升长序列任务上的建模能力。
>
> 实验表明，该方法在Long Range Arena 等长序列基准上取得优于现有方法的表现，能够实现多项长序列任务上的最优表现，并首次解决了 16k 长度的 Path-X 任务，验证了其有效性与通用性。

终端（stderr）里同时会打印判定自检结果：

```
—— 判：三句话是否覆盖问题/方法/证据 ——
✅ 问题 (Why): 第1句
✅ 方法 (How): 第2句
✅ 证据 (So what): 第3句
```

## 小提示
渲染结果是机械拼接的，中英文混排处偶尔会缺一个空格（比如"提出S4"）。这是预期的——脚本只
保证结构、变量和判定关键词都对，最后过一遍微调断句/空格是人的工作。
