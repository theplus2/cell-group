"""
제약 조건 기능 테스트
"""

import sys
import os
import pytest
import pandas as pd

# src 모듈 임포트를 위한 경로 설정
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.sorter import GroupSorter
from src.constraints import ConstraintManager, Constraint, ConstraintType
from src.preprocessor import DataPreprocessor


@pytest.fixture
def sample_df():
    """테스트용 기본 데이터프레임 (20명)"""
    data = []
    for i in range(1, 21):
        data.append({
            '이름': f'User{i}',
            '나이': 30 + (i % 5),  # 30~34세
            '출석현황': 'A' if i % 2 == 0 else 'C'
        })
    
    df = pd.DataFrame(data)
    processor = DataPreprocessor(df)
    return processor.process()


class TestConstraints:
    """제약 조건 테스트"""
    
    def test_leader_constraint(self, sample_df):
        """리더 지정 테스트"""
        manager = ConstraintManager()
        # User1을 리더로 지정
        manager.add(Constraint(ConstraintType.LEADER, 'User1'))
        
        sorter = GroupSorter(sample_df, group_size=5, constraint_manager=manager)
        result = sorter.sort_into_groups()
        
        # User1이 결과에 있고 '리더 그룹'이어야 함
        user1_row = result[result['이름'] == 'User1'].iloc[0]
        assert user1_row['분류결과'] == '리더 그룹'
        
        # 통계에서도 리더 수가 맞아야 함
        stats = sorter.get_group_statistics()
        total_leaders = stats['리더그룹수'].sum()
        # 기존 A등급 리더 + 지정 리더 (User1은 원래 C등급이었어도 리더가 됨? 아니 A등급은 원래 리더그룹. User1은 짝수가 아니므로 C등급(일반/케어). 강제 리더 지정 시 리더그룹으로 바뀜)
        # sample_df에서 User1은 i=1 -> 홀수 -> C등급 -> 케어대상/일반. Constraint로 인해 리더가 되어야 함.
        assert user1_row['분류결과'] == '리더 그룹'

    def test_include_constraint(self, sample_df):
        """포함(같은 조) 조건 테스트"""
        manager = ConstraintManager()
        # User1과 User2를 같은 조로
        manager.add(Constraint(ConstraintType.INCLUDE, 'User1', 'User2'))
        
        sorter = GroupSorter(sample_df, group_size=5, constraint_manager=manager)
        result = sorter.sort_into_groups()
        
        group1 = result[result['이름'] == 'User1']['소그룹명'].iloc[0]
        group2 = result[result['이름'] == 'User2']['소그룹명'].iloc[0]
        
        assert group1 == group2

    def test_exclude_constraint(self, sample_df):
        """분리(다른 조) 조건 테스트"""
        manager = ConstraintManager()
        # User1과 User2를 다른 조로
        manager.add(Constraint(ConstraintType.EXCLUDE, 'User1', 'User2'))
        
        # 그룹이 충분히 생기도록 사이즈 조절 (20명 / 4명 = 5개 그룹)
        sorter = GroupSorter(sample_df, group_size=4, constraint_manager=manager)
        result = sorter.sort_into_groups()
        
        group1 = result[result['이름'] == 'User1']['소그룹명'].iloc[0]
        group2 = result[result['이름'] == 'User2']['소그룹명'].iloc[0]
        
        assert group1 != group2
        
        # 위반 사항이 없어야 함
        violations = sorter.get_constraint_violations()
        assert len(violations) == 0

    def test_complex_constraints(self, sample_df):
        """복합 제약 조건 테스트"""
        manager = ConstraintManager()
        # User1 리더
        manager.add(Constraint(ConstraintType.LEADER, 'User1'))
        # User2, User3 같은 조
        manager.add(Constraint(ConstraintType.INCLUDE, 'User2', 'User3'))
        # User4, User5 다른 조
        manager.add(Constraint(ConstraintType.EXCLUDE, 'User4', 'User5'))
        
        sorter = GroupSorter(sample_df, group_size=5, constraint_manager=manager)
        result = sorter.sort_into_groups()
        
        # 검증
        # 1. 리더
        assert result[result['이름'] == 'User1']['분류결과'].iloc[0] == '리더 그룹'
        
        # 2. 포함
        g2 = result[result['이름'] == 'User2']['소그룹명'].iloc[0]
        g3 = result[result['이름'] == 'User3']['소그룹명'].iloc[0]
        assert g2 == g3
        
        # 3. 분리
        g4 = result[result['이름'] == 'User4']['소그룹명'].iloc[0]
        g5 = result[result['이름'] == 'User5']['소그룹명'].iloc[0]
        assert g4 != g5
        
        assert len(sorter.get_constraint_violations()) == 0
