"""
소그룹 편성 알고리즘 테스트
"""

import pandas as pd
import pytest
from src.preprocessor import DataPreprocessor
from src.sorter import GroupSorter


class TestDataPreprocessor:
    """데이터 전처리 테스트"""
    
    def test_clean_age_with_valid_data(self):
        """정상적인 나이 데이터 정제 테스트"""
        df = pd.DataFrame({
            '이름': ['김철수', '이영희'],
            '나이': [30, 25],
            '출석현황': ['A', 'B']
        })
        
        processor = DataPreprocessor(df)
        result = processor.clean_age().df
        
        assert '나이_정제' in result.columns
        assert result['나이_정제'].iloc[0] == 30
        assert result['나이_정제'].iloc[1] == 25
    
    def test_clean_age_with_invalid_data(self):
        """비정상 나이 데이터 처리 테스트"""
        df = pd.DataFrame({
            '이름': ['김철수', '이영희', '박민수'],
            '나이': [30, '불명', -5],
            '출석현황': ['A', 'B', 'C']
        })
        
        processor = DataPreprocessor(df)
        result = processor.clean_age().df
        
        # 비정상값은 평균(30)으로 대체
        assert result['나이_정제'].iloc[1] == 30
        assert result['나이_정제'].iloc[2] == 30
    
    def test_attendance_grade_conversion(self):
        """출석현황 등급 -> 점수 변환 테스트"""
        df = pd.DataFrame({
            '이름': ['김철수', '이영희', '박민수', '최지영'],
            '나이': [30, 25, 35, 28],
            '출석현황': ['A', 'B', 'C', 'D']
        })
        
        processor = DataPreprocessor(df)
        result = processor.convert_attendance_to_score().df
        
        assert result['출석점수'].iloc[0] == 4  # A
        assert result['출석점수'].iloc[1] == 3  # B
        assert result['출석점수'].iloc[2] == 2  # C
        assert result['출석점수'].iloc[3] == 1  # D


class TestGroupSorter:
    """소그룹 편성 테스트"""
    
    def test_basic_sorting(self):
        """기본 편성 테스트"""
        df = pd.DataFrame({
            '이름': ['김철수', '이영희', '박민수', '최지영', '정수진'],
            '나이_정제': [30, 31, 32, 29, 28],
            '출석점수': [4, 3, 2, 4, 1],
            '출석현황': ['A', 'B', 'C', 'A', 'D'],
            '분류결과': ['리더 그룹', '일반', '일반', '리더 그룹', '케어 대상']
        })
        
        sorter = GroupSorter(df, group_size=3)
        result = sorter.sort_into_groups()
        
        assert '소그룹명' in result.columns
        assert len(result) == 5
    
    def test_group_statistics(self):
        """그룹 통계 생성 테스트"""
        df = pd.DataFrame({
            '이름': ['김철수', '이영희', '박민수'],
            '나이_정제': [30, 31, 32],
            '출석점수': [4, 3, 1],
            '출석현황': ['A', 'B', 'D'],
            '분류결과': ['리더 그룹', '일반', '케어 대상']
        })
        
        sorter = GroupSorter(df, group_size=5)
        sorter.sort_into_groups()
        stats = sorter.get_group_statistics()
        
        assert '인원수' in stats.columns
        assert '평균나이' in stats.columns
        assert '리더그룹수' in stats.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
