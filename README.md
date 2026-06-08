# 嵌入式手势识别控制系统

基于 MediaPipe + KNN 的嵌入式视觉手势识别控制系统，运行于嵌入式 Linux 开发板。

## 功能

- 摄像头实时采集手部图像
- MediaPipe Hands 提取 21 个手部关键点
- 归一化 + 距离/角度特征工程
- KNN 分类器识别 8 种手势（数字1-5、OK、点赞、握拳）
- GPIO 控制 LED、风扇、蜂鸣器等外设
- 连续帧确认防误触发

## 项目结构

```
├── src/                    # 源代码
│   ├── capture/            # 图像采集模块
│   ├── detection/          # MediaPipe 关键点检测
│   ├── features/           # 特征提取与归一化
│   ├── classifier/         # KNN 分类器
│   ├── control/            # GPIO 外设控制
│   └── main.py             # 主程序入口
├── data/
│   ├── raw/                # 原始手势图片
│   ├── processed/          # 处理后的特征数据
│   └── models/             # 训练好的模型
├── experiments/            # 五个实验脚本
├── scripts/
│   ├── collect_data.py     # 数据采集
│   └── train.py            # 模型训练
├── config/config.yaml      # 配置文件
└── requirements.txt        # Python 依赖
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 采集数据

```bash
python scripts/collect_data.py --gesture 数字1 --count 400
```

### 3. 训练模型

```bash
python scripts/train.py --k 5 --feature all
```

### 4. 运行系统

```bash
python src/main.py
```

## 手势控制映射

| 手势 | 控制动作 |
|------|---------|
| 数字1 | LED 打开 |
| 数字2 | LED 关闭 |
| 数字3 | 风扇启动 |
| 数字4 | 风扇停止 |
| OK手势 | 蜂鸣器鸣叫 |
| 点赞 | 欢迎模式 |
| 握拳 | 全部关闭 |

## 实验

| 编号 | 实验内容 |
|------|---------|
| 实验一 | MediaPipe 关键点检测 |
| 实验二 | KNN 分类性能 |
| 实验三 | 特征选择对比 |
| 实验四 | 实时识别测试 |
| 实验五 | 外设控制测试 |
