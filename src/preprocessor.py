"""
데이터 전처리 모듈
- 나이 데이터 정제
- 출석현황 점수화 (52주 기준 출석 횟수)
- 예외 데이터 처리
"""

import pandas as pd
import numpy as np
from typing import Dict


class DataPreprocessor:
    """데이터 전처리 클래스"""
    
    # 출석 등급 기준 (52주 기준)
    # A: 40회 이상, B: 30회 이상, C: 20회 이상, D: 10회 이상, 케어대상: 10회 미만
    ATTENDANCE_THRESHOLDS = {
        'A': 40,  # 40회 이상
        'B': 30,  # 30회 이상
        'C': 20,  # 20회 이상
        'D': 10,  # 10회 이상
    }
    
    # 등급별 점수 (정렬/비교용)
    ATTENDANCE_SCORE_MAP = {
        'A': 5,
        'B': 4,
        'C': 3,
        'D': 2,
        '케어대상': 1,
    }
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.processed_df: pd.DataFrame = None
    
    def clean_age(self) -> 'DataPreprocessor':
        """
        나이 데이터를 정제합니다.
        - 숫자가 아닌 값은 평균 나이로 대체
        - 비정상 범위(0 이하, 150 이상) 처리
        """
        # 숫자로 변환 시도
        self.df['나이_정제'] = pd.to_numeric(self.df['나이'], errors='coerce')
        
        # 유효한 나이 값만으로 평균 계산
        valid_ages = self.df['나이_정제'].dropna()
        valid_ages = valid_ages[(valid_ages > 0) & (valid_ages < 150)]
        mean_age = int(valid_ages.mean()) if len(valid_ages) > 0 else 30
        
        # 결측치 및 무효 값 대체
        mask = self.df['나이_정제'].isna() | (self.df['나이_정제'] <= 0) | (self.df['나이_정제'] >= 150)
        self.df.loc[mask, '나이_정제'] = mean_age
        
        self.df['나이_정제'] = self.df['나이_정제'].astype(int)
        
        return self
    
    def convert_attendance_to_score(self) -> 'DataPreprocessor':
        """
        출석현황을 등급 및 점수로 변환합니다.
        - 숫자(출석 횟수)인 경우: 52주 기준으로 등급 산정
        - 등급(A/B/C/D)인 경우: 기존 등급 유지
        """
        def convert_value(val):
            # None 또는 NaN 처리
            if pd.isna(val):
                return 3, 'C'  # 기본값
            
            # 문자열인 경우 등급으로 해석
            if isinstance(val, str):
                val_upper = val.upper().strip()
                if val_upper in self.ATTENDANCE_SCORE_MAP:
                    return self.ATTENDANCE_SCORE_MAP[val_upper], val_upper
                # 숫자로 변환 시도
                try:
                    attendance_count = int(val)
                except ValueError:
                    return 3, 'C'
            else:
                try:
                    attendance_count = int(val)
                except (ValueError, TypeError):
                    return 3, 'C'
            
            # 출석 횟수 -> 등급 변환
            if attendance_count >= self.ATTENDANCE_THRESHOLDS['A']:
                return self.ATTENDANCE_SCORE_MAP['A'], 'A'
            elif attendance_count >= self.ATTENDANCE_THRESHOLDS['B']:
                return self.ATTENDANCE_SCORE_MAP['B'], 'B'
            elif attendance_count >= self.ATTENDANCE_THRESHOLDS['C']:
                return self.ATTENDANCE_SCORE_MAP['C'], 'C'
            elif attendance_count >= self.ATTENDANCE_THRESHOLDS['D']:
                return self.ATTENDANCE_SCORE_MAP['D'], 'D'
            else:
                return self.ATTENDANCE_SCORE_MAP['케어대상'], '케어대상'
        
        results = self.df['출석현황'].apply(convert_value)
        self.df['출석점수'] = [r[0] for r in results]
        self.df['출석등급'] = [r[1] for r in results]
        
        return self
    
    def categorize_role(self) -> 'DataPreprocessor':
        """
        출석등급을 기반으로 역할을 분류합니다.
        - 케어 대상: 10회 미만 출석
        - 일반: 그 외 모두 (리더는 sorter에서 조별로 자동 선정)
        """
        def assign_role(등급):
            if 등급 == '케어대상':
                return '케어 대상'
            else:
                return '일반'
        
        self.df['분류결과'] = self.df['출석등급'].apply(assign_role)
        
        return self
    
    def process(self) -> pd.DataFrame:
        """
        모든 전처리를 수행하고 결과를 반환합니다.
        """
        self.clean_age()
        self.convert_attendance_to_score()
        self.categorize_role()
        
        self.processed_df = self.df
        return self.processed_df

