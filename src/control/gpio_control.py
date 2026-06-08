"""
GPIO外设控制模块 - GPIO Peripheral Control Module
根据手势识别结果控制 LED、风扇、蜂鸣器等设备
"""

import time
from typing import Dict, Optional

# 嵌入式平台GPIO库（开发阶段可使用模拟模式）
try:
    import RPi.GPIO as GPIO
    _GPIO_AVAILABLE = True
except ImportError:
    _GPIO_AVAILABLE = False
    # 模拟 GPIO 用于非嵌入式开发环境
    class _MockGPIO:
        BCM = "BCM"
        BOARD = "BOARD"
        OUT = "OUT"
        IN = "IN"
        HIGH = True
        LOW = False
        _pins = {}

        @staticmethod
        def setmode(mode): pass

        @staticmethod
        def setup(pin, mode, initial=None):
            _MockGPIO._pins[pin] = initial if initial is not None else False

        @staticmethod
        def output(pin, state):
            _MockGPIO._pins[pin] = state

        @staticmethod
        def input(pin):
            return _MockGPIO._pins.get(pin, False)

        @staticmethod
        def cleanup():
            _MockGPIO._pins.clear()

    GPIO = _MockGPIO


class GPIOController:
    """
    GPIO设备控制器

    管理手势与外设的映射关系，带连续帧确认防误触发
    """

    # GPIO引脚定义 (BCM编号)
    PIN_LED = 17       # LED
    PIN_FAN = 18       # 风扇
    PIN_BUZZER = 27    # 蜂鸣器

    # 手势→控制动作映射
    GESTURE_ACTIONS = {
        "数字1":    ("led", "on"),
        "数字2":    ("led", "off"),
        "数字3":    ("fan", "on"),
        "数字4":    ("fan", "off"),
        "OK手势":   ("buzzer", "beep"),
        "点赞手势": ("welcome", None),
        "握拳手势": ("all_off", None),
    }

    def __init__(self, confirm_frames: int = 5):
        """
        初始化GPIO控制器

        Args:
            confirm_frames: 连续识别确认帧数，防止误触发
        """
        self.confirm_frames = confirm_frames
        self._last_gesture: Optional[str] = None
        self._confirm_count: int = 0
        self._state: Dict[str, bool] = {"led": False, "fan": False}
        self._init_gpio()

    def _init_gpio(self):
        """初始化GPIO引脚"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN_LED, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.PIN_FAN, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.PIN_BUZZER, GPIO.OUT, initial=GPIO.LOW)

    def execute(self, gesture_name: str) -> Optional[str]:
        """
        执行手势对应的控制动作（含连续帧确认）

        Args:
            gesture_name: 识别到的手势名称

        Returns:
            执行的动作描述，或 None（确认中/无动作）
        """
        # 连续帧确认逻辑
        if gesture_name == self._last_gesture:
            self._confirm_count += 1
        else:
            self._last_gesture = gesture_name
            self._confirm_count = 1
            return None  # 新手势，开始计数

        if self._confirm_count < self.confirm_frames:
            return None  # 未达到确认帧数

        # 达到确认帧数，执行动作
        action = self.GESTURE_ACTIONS.get(gesture_name)
        if action is None:
            return None

        device, cmd = action
        desc = self._do_action(device, cmd)
        return desc

    def _do_action(self, device: str, cmd: str) -> str:
        """执行具体设备控制"""
        if device == "led":
            if cmd == "on":
                GPIO.output(self.PIN_LED, GPIO.HIGH)
                self._state["led"] = True
                return "LED 已打开"
            elif cmd == "off":
                GPIO.output(self.PIN_LED, GPIO.LOW)
                self._state["led"] = False
                return "LED 已关闭"

        elif device == "fan":
            if cmd == "on":
                GPIO.output(self.PIN_FAN, GPIO.HIGH)
                self._state["fan"] = True
                return "风扇 已启动"
            elif cmd == "off":
                GPIO.output(self.PIN_FAN, GPIO.LOW)
                self._state["fan"] = False
                return "风扇 已停止"

        elif device == "buzzer":
            if cmd == "beep":
                GPIO.output(self.PIN_BUZZER, GPIO.HIGH)
                time.sleep(0.3)
                GPIO.output(self.PIN_BUZZER, GPIO.LOW)
                return "蜂鸣器 鸣叫"

        elif device == "welcome":
            # 欢迎模式：LED闪烁 + 蜂鸣器短鸣
            for _ in range(3):
                GPIO.output(self.PIN_LED, GPIO.HIGH)
                GPIO.output(self.PIN_BUZZER, GPIO.HIGH)
                time.sleep(0.15)
                GPIO.output(self.PIN_LED, GPIO.LOW)
                GPIO.output(self.PIN_BUZZER, GPIO.LOW)
                time.sleep(0.15)
            return "欢迎模式 已触发"

        elif device == "all_off":
            GPIO.output(self.PIN_LED, GPIO.LOW)
            GPIO.output(self.PIN_FAN, GPIO.LOW)
            GPIO.output(self.PIN_BUZZER, GPIO.LOW)
            self._state["led"] = False
            self._state["fan"] = False
            return "所有设备 已关闭"

        return f"未知指令: {device}/{cmd}"

    def cleanup(self):
        """清理GPIO资源"""
        GPIO.cleanup()
