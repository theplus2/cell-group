"""
제약 조건 모듈
- 포함(같은 조), 분리(다른 조), 리더 지정 제약 조건 관리
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple
import pandas as pd


class ConstraintType(Enum):
    """제약 조건 유형"""
    INCLUDE = "포함"   # 같은 조에 배정해야 함
    EXCLUDE = "분리"   # 다른 조에 배정해야 함
    LEADER = "리더"    # 조 리더로 지정


@dataclass
class Constraint:
    """개별 제약 조건"""
    type: ConstraintType
    person1: str                        # 대상1 이름
    person2: Optional[str] = None       # 대상2 (리더 유형은 None)
    note: str = ""                      # 메모/사유
    
    def __post_init__(self):
        # 이름 공백 정규화
        self.person1 = self.person1.strip() if self.person1 else ""
        if self.person2:
            self.person2 = self.person2.strip()
    
    def involves(self, name: str) -> bool:
        """해당 이름이 이 제약 조건에 관련되어 있는지 확인"""
        name = name.strip()
        return name == self.person1 or name == self.person2
    
    def get_pair(self) -> Tuple[str, Optional[str]]:
        """(person1, person2) 튜플 반환"""
        return (self.person1, self.person2)


@dataclass
class ConstraintManager:
    """제약 조건 관리자"""
    constraints: List[Constraint] = field(default_factory=list)
    
    @property
    def include_constraints(self) -> List[Constraint]:
        """포함 조건 목록"""
        return [c for c in self.constraints if c.type == ConstraintType.INCLUDE]
    
    @property
    def exclude_constraints(self) -> List[Constraint]:
        """분리 조건 목록"""
        return [c for c in self.constraints if c.type == ConstraintType.EXCLUDE]
    
    @property
    def leader_constraints(self) -> List[Constraint]:
        """리더 지정 목록"""
        return [c for c in self.constraints if c.type == ConstraintType.LEADER]
    
    def add(self, constraint: Constraint):
        """제약 조건 추가"""
        self.constraints.append(constraint)
    
    def remove(self, index: int):
        """인덱스로 제약 조건 삭제"""
        if 0 <= index < len(self.constraints):
            self.constraints.pop(index)
    
    def clear(self):
        """모든 제약 조건 삭제"""
        self.constraints.clear()
    
    def get_leaders(self) -> Set[str]:
        """리더로 지정된 이름 집합 반환"""
        return {c.person1 for c in self.leader_constraints}
    
    def get_include_pairs(self) -> List[Tuple[str, str]]:
        """포함 쌍 목록 반환"""
        return [(c.person1, c.person2) for c in self.include_constraints if c.person2]
    
    def get_exclude_pairs(self) -> List[Tuple[str, str]]:
        """분리 쌍 목록 반환"""
        return [(c.person1, c.person2) for c in self.exclude_constraints if c.person2]
    
    def validate_names(self, valid_names: Set[str]) -> List[str]:
        """
        유효한 이름 목록과 비교하여 매칭되지 않는 이름 반환
        
        Args:
            valid_names: 유효한 이름 집합 (교인 명단에서 추출)
            
        Returns:
            매칭 실패한 이름 목록
        """
        # 이름 정규화 (공백 제거)
        normalized_valid = {name.strip() for name in valid_names}
        invalid_names = []
        
        for constraint in self.constraints:
            if constraint.person1 and constraint.person1 not in normalized_valid:
                invalid_names.append(constraint.person1)
            if constraint.person2 and constraint.person2 not in normalized_valid:
                invalid_names.append(constraint.person2)
        
        return list(set(invalid_names))
    
    def to_dataframe(self) -> pd.DataFrame:
        """DataFrame으로 변환 (엑셀 저장용)"""
        data = []
        for c in self.constraints:
            data.append({
                '유형': c.type.value,
                '대상1': c.person1,
                '대상2': c.person2 or '',
                '메모': c.note
            })
        return pd.DataFrame(data)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> 'ConstraintManager':
        """DataFrame에서 생성"""
        manager = cls()
        
        if df is None or df.empty:
            return manager
        
        for _, row in df.iterrows():
            type_str = str(row.get('유형', '')).strip()
            person1 = str(row.get('대상1', '')).strip()
            person2 = str(row.get('대상2', '')).strip() or None
            note = str(row.get('메모', '')).strip()
            
            # 유형 파싱
            constraint_type = None
            for ct in ConstraintType:
                if ct.value == type_str:
                    constraint_type = ct
                    break
            
            if constraint_type and person1:
                manager.add(Constraint(
                    type=constraint_type,
                    person1=person1,
                    person2=person2 if person2 and person2 != 'nan' else None,
                    note=note if note != 'nan' else ''
                ))
        
        return manager
    
    def __len__(self) -> int:
        return len(self.constraints)
    
    def __iter__(self):
        return iter(self.constraints)
