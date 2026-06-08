"""
手势识别控制系统 - 主程序
Gesture Recognition Control System - Main Entry

运行流程:
    摄像头采集 → 手部检测 → 特征提取 → 手势分类 → GPIO控制 → 结果显示
"""

import sys
import time
import argparse
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.capture import Camera
from src.detection import HandDetector
from src.features import FeatureExtractor
from src.classifier import KNNClassifier
from src.control import GPIOController


def parse_args():
    parser = argparse.ArgumentParser(description="手势识别控制系统")
    parser.add_argument("--camera", type=int, default=0, help="摄像头ID")
    parser.add_argument("--model", type=str, default="data/models/knn_model.pkl",
                        help="训练好的KNN模型路径")
    parser.add_argument("--k", type=int, default=5, help="KNN的K值（未加载模型时使用）")
    parser.add_argument("--confirm", type=int, default=5,
                        help="连续确认帧数（防误触发）")
    parser.add_argument("--no-control", action="store_true",
                        help="禁用GPIO控制（纯识别模式）")
    parser.add_argument("--feature", type=str, default="all",
                        choices=["distance", "angle", "all"],
                        help="特征集类型")
    return parser.parse_args()


def main():
    args = parse_args()

    # 初始化各模块
    print("=" * 50)
    print("手势识别控制系统 v0.1.0")
    print("=" * 50)

    # 1. 分类器
    classifier = KNNClassifier(k=args.k)
    model_path = Path(args.model)
    if model_path.exists():
        print(f"[INFO] 加载模型: {model_path}")
        classifier.load(str(model_path))
    else:
        print(f"[WARN] 模型文件不存在: {model_path}")
        print("[WARN] 请先运行 train.py 训练模型，当前仅做关键点检测演示")

    # 2. 检测器
    detector = HandDetector(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
    )

    # 3. 特征提取器
    extractor = FeatureExtractor()

    # 4. GPIO控制器
    controller = None if args.no_control else GPIOController(
        confirm_frames=args.confirm
    )

    # 5. 摄像头
    camera = Camera(camera_id=args.camera)

    try:
        if not camera.open():
            print("[ERROR] 无法打开摄像头")
            return

        print("[INFO] 系统就绪，按 'q' 退出")
        frame_count = 0
        start_time = time.time()

        while True:
            success, frame = camera.read()
            if not success:
                print("[WARN] 读取帧失败")
                continue

            # 镜像翻转（自拍视角更自然）
            frame = cv2.flip(frame, 1)

            # 手部关键点检测
            detected, landmarks = detector.detect(frame)

            gesture_text = "未检测到手部"
            action_desc = ""

            if detected and landmarks is not None:
                # 绘制关键点
                detector.draw_landmarks(frame, landmarks)

                # 特征提取
                features = extractor.extract(landmarks, args.feature)

                # 手势分类（如模型已加载）
                if classifier.trained:
                    try:
                        label, confidence = classifier.predict_with_confidence(features)
                        gesture_name = classifier.get_label_name(label)
                        gesture_text = f"{gesture_name} ({confidence:.2f})"

                        # GPIO控制
                        if controller is not None:
                            desc = controller.execute(gesture_name)
                            if desc:
                                action_desc = desc
                    except Exception as e:
                        gesture_text = f"分类错误: {e}"
                else:
                    gesture_text = "模型未加载"

            # 帧率统计
            frame_count += 1
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0

            # 显示信息
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, gesture_text, (10, 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if action_desc:
                cv2.putText(frame, f">> {action_desc}", (10, 85),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

            cv2.imshow("Gesture Control System", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    finally:
        camera.release()
        detector.close()
        if controller is not None:
            controller.cleanup()
        cv2.destroyAllWindows()
        print(f"[INFO] 系统已停止，共处理 {frame_count} 帧")


if __name__ == "__main__":
    import cv2
    main()
