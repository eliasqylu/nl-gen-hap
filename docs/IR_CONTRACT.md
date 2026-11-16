# IR 契约与研究假设（阶段 0）

> 状态：第一版预览原型。本文档定义设备无关的中间表示（IR）、研究主线与自测指标。
> 代码对应：`app/ir_model.py`、`app/signal_preview.py`、`app/llm_interface.py`。

## 1. 目标与范围

**研究主线（方向一）**：局部编辑振动反馈时，识别要改变的感受与要保留的感受，通过补偿调整压低无关变化；用感知证据验证目标感受按要求改变、保留感受更稳定。

**二期（方向二，本版不做）**：跨设备按设计意图优先级选择性保留特征。

**第一版非目标**：真实硬件振动输出、跨设备适配、受试者统计实验、高保真波形合成。当前仅在本机做 IR 编辑与波形预览。

## 2. 四层管线

```
感受层 SensationProfile  —— 设备无关，主观属性（粗糙度/愉悦/唤醒/能量/节奏 + 标签）
结构层 HapticTrack       —— 设备无关，事件块序列（类型/强度/频率/时长/波形/包络/通道）
设备信号层               —— 各后端翻译：预览波形（当前）→ DS / ERM 后端（后续）
试震比较层               —— 编辑前后对比、感知评分（当前自测，后续受试者实验）
```

标准化落在**感受层与结构层**，不在波形层：同一 IR 可翻译成不同执行器的信号；波形绑定具体设备，不进入 IR。

## 3. IR 字段契约

### 3.1 感受层 `SensationProfile`

| 字段 | 类型 | 取值 | 说明 |
|---|---|---|---|
| roughness | int | 1–5 | 1 very smooth … 5 very rough |
| valence | int | 1–5 | 1 unpleasant … 5 pleasant |
| arousal | int | 1–5 | 1 calm … 5 exciting |
| energy | int | 1–5 | 1 low … 5 high |
| tempo | enum | slow / medium / fast | 节奏速度 |
| metaphor_tags | list[str] | — | 隐喻词（敲击/鼓/心跳…） |
| scenario_tags | list[str] | — | 场景词（受击/提醒/落地…） |

### 3.2 结构层 `HapticTrack`

| 字段 | 类型 | 说明 |
|---|---|---|
| track_id / title | str | 标识与名称 |
| repeats | int ≥1 | 整段重复次数 |
| channel | enum | a / b / ab（左右/双通道，预览阶段暂不分离波形） |
| blocks | list[HapticBlock] | 事件序列，按时间顺序 |

### 3.3 事件块 `HapticBlock`

| 字段 | 类型 | 取值/范围 | 说明 |
|---|---|---|---|
| type | enum | vibration / pulse / pause | 持续振动 / 离散脉冲 / 静默间隔 |
| duration | float? | 秒 | pause、vibration 必填；pulse 可省略（默认 0.06s） |
| waveform | enum | sine / saw / none | 载波波形 |
| intensity | float | 0–1 | 基底强度 |
| frequency | float | 50–500 Hz | 载波/主频 |
| envelope | Envelope | 见下 | 强度/频率包络 |

`Envelope`：`intensity_curve`、`freq_curve`（flat / ramp_up / ramp_down / up_down），`attack`、`release`（秒，预留）。

### 3.4 编辑意图 `EditIntent`（方向一预留）

| 字段 | 说明 |
|---|---|
| target_sensations | 要改变的感受维度（取自 `SENSATION_DIMENSIONS`） |
| preserve_sensations | 要保持稳定的感受维度 |
| direction | 自然语言方向（stronger / rougher / slower…） |
| rationale | 调整理由记录 |

## 4. 借鉴来源与自研边界

| 部分 | 来源 | 处理 |
|---|---|---|
| 块式事件序列、双通道、独立强度/频率包络 | 参考 Hapticlabs 本地 IR（`.hlabs` JSON） | 借鉴结构思路；参数范围、波形集、包络模型按本项目重做 |
| 感受量表维度（roughness/valence/arousal/energy/tempo）+ 隐喻/场景标签 | 参考 ChatHAP 样本标注体系 | 借鉴维度划分；不沿用其感受→参数的硬编码映射 |
| 补偿编辑（改目标感受、守保留感受） | **自研，方向一核心** | 现有原型均未解决 |
| 跨设备意图保留 | **自研，方向二二期** | 现有工具仅做频段裁剪 |
| 信号合成 / 设备后端 | 自研 | 不继承 ChatHAP 的 NI DAQ 输出与单通道假设 |

## 5. 研究假设与变量

### 假设
- **H1 目标改变**：补偿编辑法相比直接调参、普通对话修改，目标感受维度的前后评分变化更显著。
- **H2 保留稳定**：保留感受维度在编辑前后的评分波动（绝对差）更小。
- **H3 主观偏好**：受试者更偏好补偿编辑结果（后续受试者阶段检验）。

### 变量
- **自变量**：编辑方法三档 —— 补偿编辑法 / 直接参数法 / 普通对话法。
- **因变量**：目标维度前后评分差；保留维度前后评分绝对差；主观偏好评分。
- **控制**：同一初始轨道、同一目标修改指令、同一设备预览条件。

### 第一版自测（作者本人，不做统计推断）
- 在样例轨道上用三种方式完成同一修改指令；
- 记录目标/保留维度 1–5 评分前后值；
- 目的：跑通 IR→预览→对比流程，暴露 schema、合成与交互问题，不产出结论性数据。

## 6. 待验证风险

1. **DeepSeek 结构化遵循度**：生成链已在 ChatHAP 对照验证可行；本项目 `HapticTrack` 嵌套 schema 的解析稳定性需实测，必要时换模型或加 JSON 兜底解析。
2. **预览合成保真度**：当前块叠加波形仅用于结构预览，不代表真实执行器感受；不能据预览波形判断跨设备表现。
3. **感受—参数映射未标定**：IR 字段到主观感受的对应关系尚需实验建立；第一版不预设固定映射规则。
4. **DS 高保真链路**：需 Windows 环境 + GameInput/社区库；Mac 本机仅能做基础双马达与预览。
