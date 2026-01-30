"""
설정 모듈
- 시스템 기본값 정의
- 사용자 설정 관리
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class SorterConfig:
    """소그룹 편성 설정"""

    # 앱 버전 (Single Source of Truth)
    APP_VERSION: str = "3.0.0"
    
    # 그룹당 목표 인원
    group_size: int = 10
    
    # 그룹 내 허용 나이 차이 (±N살)
    age_tolerance: int = 5
    
    # 출석현황 등급 -> 점수 매핑
    attendance_grade_map: Dict[str, int] = None
    
    # 출력 파일 기본 이름
    output_filename: str = "sorted_result.xlsx"
    
    def __post_init__(self):
        if self.attendance_grade_map is None:
            self.attendance_grade_map = {
                'A': 4,  # 매주 출석
                'B': 3,  # 월 2-3회
                'C': 2,  # 가끔
                'D': 1,  # 장기결석
            }


# 기본 설정 인스턴스
DEFAULT_CONFIG = SorterConfig()
