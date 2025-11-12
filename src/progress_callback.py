"""
진행 상황 콜백 핸들러
"""
from typing import Callable, Optional


class ProgressCallback:
    """진행 상황을 전달하기 위한 콜백 클래스"""

    def __init__(self, callback: Optional[Callable[[str, float], None]] = None):
        """
        Args:
            callback: 진행 상황을 받을 콜백 함수 (message: str, progress: float)
        """
        self.callback = callback

    def update(self, message: str, progress: float = None):
        """
        진행 상황 업데이트

        Args:
            message: 표시할 메시지
            progress: 진행률 (0.0 ~ 1.0), None이면 진행률 표시 안 함
        """
        if self.callback:
            self.callback(message, progress)
        else:
            # 콜백이 없으면 콘솔에 출력
            print(message)
