# NL Gen Hap

面向游戏开发者的自然语言振动反馈设计原型。研究主线：**局部编辑的感受解耦与补偿控制**（改目标感受，守住保留感受）。

> 第一版为本机 DEBUG 波形预览原型，不输出真实振动，不做跨设备适配。详见 [`docs/IR_CONTRACT.md`](docs/IR_CONTRACT.md)。

## 目录

```
app/
  ir_model.py        # 设备无关 IR 数据模型（感受层 / 结构层 / 编辑意图）
  signal_preview.py  # IR → 预览波形（numpy，不接硬件）
  llm_interface.py   # OpenAI 兼容模型接口（DeepSeek），生成链已接通，修改链预留
  main.py            # Streamlit 入口
docs/
  IR_CONTRACT.md     # IR 契约、研究假设、变量与自测指标
```

## 启动

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # 填入 OPENAI_API_KEY
.venv/bin/python -m streamlit run app/main.py --server.address 127.0.0.1
```

## 当前状态

- [x] IR 数据模型与内置样例（落水 / 重击）
- [x] 波形预览与 IR/评分查看
- [x] DeepSeek 生成链（NL → HapticTrack）
- [ ] 补偿编辑与前后对比（方向一核心）
- [ ] 设备后端（ERM 双马达 / DS，二期）
- [ ] 感知实验（受试者阶段）

## 边界

- 预览波形仅用于结构核对，不代表真实执行器感受。
- 密钥仅存本机 `.env`（已 gitignore），不进入版本库。
