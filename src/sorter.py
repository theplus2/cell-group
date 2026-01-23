"""
소그룹 편성 알고리즘 모듈
- 나이 기반 또래 편성
- 출석점수 균등 분배 (S자형 배치)
- 제약 조건 처리 (리더/포함/분리)
"""

import re
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Set, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .constraints import ConstraintManager


class GroupSorter:
    """소그룹 편성 알고리즘 클래스"""
    
    def __init__(
        self, 
        df: pd.DataFrame, 
        group_size: int = 10, 
        age_tolerance: int = 5,
        constraint_manager: Optional['ConstraintManager'] = None
    ):
        """
        Args:
            df: 전처리된 교인 데이터프레임
            group_size: 그룹당 목표 인원
            age_tolerance: 그룹 내 허용 나이 차이 (±N살)
            constraint_manager: 제약 조건 관리자 (선택)
        """
        self.df = df.copy()
        self.group_size = group_size
        self.age_tolerance = age_tolerance
        self.constraint_manager = constraint_manager
        self.result_df: pd.DataFrame = None
        
        # 이름 → 인덱스 매핑
        self._name_to_idx: Dict[str, int] = {}
        self._build_name_index()
    
    def _build_name_index(self):
        """이름으로 DataFrame 인덱스를 찾기 위한 매핑 생성"""
        if '이름' in self.df.columns:
            for idx, name in enumerate(self.df['이름']):
                self._name_to_idx[str(name).strip()] = idx
    
    def _create_age_bands(self) -> List[Tuple[int, int]]:
        """나이 밴드를 생성합니다."""
        min_age = self.df['나이_정제'].min()
        max_age = self.df['나이_정제'].max()
        
        bands = []
        current = min_age
        band_size = self.age_tolerance * 2
        
        while current <= max_age:
            band_end = min(current + band_size, max_age + 1)
            bands.append((current, band_end))
            current = band_end
        
        return bands
    
    def _snake_sort(self, members: pd.DataFrame, num_groups: int = None) -> pd.DataFrame:
        """S자형(스네이크) 배치 알고리즘"""
        sorted_members = members.sort_values('출석점수', ascending=False).reset_index(drop=True)
        
        num_members = len(sorted_members)
        if num_groups is None:
            num_groups = max(1, (num_members + self.group_size - 1) // self.group_size)
        
        group_assignments = []
        
        for idx in range(num_members):
            row = idx // num_groups
            pos_in_row = idx % num_groups
            
            if row % 2 == 0:
                group_num = pos_in_row
            else:
                group_num = num_groups - 1 - pos_in_row
            
            group_assignments.append(group_num)
        
        sorted_members['그룹_내_번호'] = group_assignments
        
        return sorted_members
    
    def _apply_leader_constraints(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Set[str]]:
        """
        리더 제약 조건 적용: 리더로 지정된 인원을 별도로 분리
        
        Returns:
            (리더 제외된 DataFrame, 리더 이름 집합)
        """
        if self.constraint_manager is None:
            return df, set()
        
        leaders = self.constraint_manager.get_leaders()
        if not leaders:
            return df, set()
        
        # 리더 제외
        leader_mask = df['이름'].astype(str).str.strip().isin(leaders)
        non_leaders = df[~leader_mask].copy()
        
        return non_leaders, leaders
    
    def _apply_include_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        포함 제약 조건 적용: 같은 조에 있어야 하는 쌍을 묶음
        person1과 같은 그룹에 person2를 배정
        """
        if self.constraint_manager is None:
            return df
        
        include_pairs = self.constraint_manager.get_include_pairs()
        if not include_pairs:
            return df
        
        result = df.copy()
        
        for person1, person2 in include_pairs:
            # person1의 그룹 찾기
            mask1 = result['이름'].astype(str).str.strip() == person1
            mask2 = result['이름'].astype(str).str.strip() == person2
            
            if mask1.any() and mask2.any():
                group1 = result.loc[mask1, '그룹_내_번호'].iloc[0]
                # person2의 그룹을 person1과 동일하게 변경
                result.loc[mask2, '그룹_내_번호'] = group1
        
        return result
    
    def _apply_exclude_constraints(self, df: pd.DataFrame, max_iterations: int = 50) -> pd.DataFrame:
        """
        분리 제약 조건 적용: 같은 조에 있으면 안 되는 쌍을 분리
        위반 시 다른 그룹의 인원과 swap
        """
        if self.constraint_manager is None:
            return df
        
        exclude_pairs = self.constraint_manager.get_exclude_pairs()
        if not exclude_pairs:
            return df
        
        result = df.copy()
        
        for _ in range(max_iterations):
            violations_fixed = True
            
            for person1, person2 in exclude_pairs:
                mask1 = result['이름'].astype(str).str.strip() == person1
                mask2 = result['이름'].astype(str).str.strip() == person2
                
                if not (mask1.any() and mask2.any()):
                    continue
                
                group1 = result.loc[mask1, '그룹_내_번호'].iloc[0]
                group2 = result.loc[mask2, '그룹_내_번호'].iloc[0]
                
                if group1 == group2:
                    # 위반! person2를 다른 그룹으로 swap
                    other_groups = result[result['그룹_내_번호'] != group1]['그룹_내_번호'].unique()
                    
                    if len(other_groups) > 0:
                        target_group = other_groups[0]
                        # 타겟 그룹에서 랜덤 인원과 swap
                        swap_candidates = result[result['그룹_내_번호'] == target_group]
                        if len(swap_candidates) > 0:
                            swap_idx = swap_candidates.index[0]
                            # person2의 그룹을 target_group으로
                            result.loc[mask2, '그룹_내_번호'] = target_group
                            # swap 대상의 그룹을 group1으로
                            result.loc[swap_idx, '그룹_내_번호'] = group1
                            violations_fixed = False
            
            if violations_fixed:
                break
        
        return result
    
    def sort_into_groups(self) -> pd.DataFrame:
        """
        전체 교인을 소그룹으로 편성합니다.
        
        v2.5 알고리즘:
        1. 포함(Include) 제약 조건 먼저 처리: 같이 있어야 할 쌍의 나이를 맞춤
        2. 나이 밴드별로 그룹화
        3. 각 밴드 내에서 조 편성 (S자형 배치, 80%~120% 규칙)
        4. 분리(Exclude) 제약 조건 후처리
        5. 리더 배정 및 자동 선정
        """
        import re
        
        # 1. 리더 분리 (제약조건으로 지정된 리더)
        working_df, designated_leaders = self._apply_leader_constraints(self.df)
        
        if len(working_df) == 0 and not designated_leaders:
            self.result_df = pd.DataFrame(columns=['소그룹명', '이름', '나이', '출석현황', '분류결과'])
            return self.result_df
        
        # 2. 포함(Include) 제약 조건 사전 처리: 쌍의 나이를 맞춤
        working_df = self._preprocess_include_constraints(working_df)
        
        # 3. 나이 밴드 생성
        age_bands = self._create_age_bands()
        
        # 4. 밴드별로 멤버 분류
        band_members = []
        for band_start, band_end in age_bands:
            mask = (working_df['나이_정제'] >= band_start) & (working_df['나이_정제'] < band_end)
            members = working_df[mask].copy()
            if len(members) > 0:
                band_members.append({
                    'band': (band_start, band_end),
                    'members': members,
                    'count': len(members)
                })
        
        # 5. 잔여 인원 병합 (80% 규칙)
        threshold = int(self.group_size * 0.8)
        merged_bands = self._merge_small_bands(band_members, threshold)
        
        # 6. 각 밴드 내에서 조 편성
        all_results = []
        global_group_counter = 1
        
        for band_info in merged_bands:
            members = band_info['members']
            if len(members) == 0:
                continue
            
            # 밴드 내 조 개수 결정 (v2.5: 80%~120% 규칙)
            band_count = len(members)
            min_per_group = max(1, int(self.group_size * 0.8))
            max_per_group = int(self.group_size * 1.2)
            
            min_groups = max(1, -(-band_count // max_per_group))
            max_groups = max(1, band_count // min_per_group)
            ideal_groups = round(band_count / self.group_size)
            num_groups_in_band = max(min_groups, min(max_groups, ideal_groups))
            
            # S자형 배치
            sorted_band = self._snake_sort(members, num_groups_in_band)
            
            # 포함 제약 조건 적용 (밴드 내)
            sorted_band = self._apply_include_constraints(sorted_band)
            
            # 전역 그룹 번호 할당
            unique_local_groups = sorted(sorted_band['그룹_내_번호'].unique())
            local_to_global = {local: global_group_counter + i 
                             for i, local in enumerate(unique_local_groups)}
            
            sorted_band['소그룹명'] = sorted_band['그룹_내_번호'].map(
                lambda x: f"{local_to_global[x]}조"
            )
            
            global_group_counter += len(unique_local_groups)
            all_results.append(sorted_band)
        
        # 7. 결과 병합
        if all_results:
            self.result_df = pd.concat(all_results, ignore_index=True)
        else:
            self.result_df = pd.DataFrame(columns=working_df.columns.tolist() + ['소그룹명'])
        
        # 8. 분리(Exclude) 제약 조건 후처리 (전체 결과에 대해)
        self._apply_exclude_constraints_global()
        
        # 9. 지정된 리더 배정
        if designated_leaders and len(self.result_df) > 0:
            self._assign_leaders_to_groups(designated_leaders, global_group_counter - 1)
        
        # 10. 리더가 없는 조에 대해 자동 리더 선정
        self._auto_assign_leaders()
        
        # 출력 컬럼 정리
        output_columns = ['소그룹명', '이름', '나이', '출석현황', '출석등급', '분류결과']
        available_columns = [col for col in output_columns if col in self.result_df.columns]
        
        if '나이' not in self.result_df.columns and '나이_정제' in self.result_df.columns:
            self.result_df['나이'] = self.result_df['나이_정제']
        
        self.result_df = self.result_df[available_columns]
        
        # 마지막으로 조별 정렬 (1조, 2조, ...)
        def natural_sort_key(s):
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split('([0-9]+)', str(s))]
        
        self.result_df = self.result_df.sort_values(
            by='소그룹명', 
            key=lambda x: x.map(natural_sort_key)
        ).reset_index(drop=True)
        
        return self.result_df
    
    def _preprocess_include_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        포함 제약 조건 사전 처리: 같이 있어야 할 쌍의 나이를 맞춤
        person2의 나이를 person1의 나이로 임시 조정하여 같은 밴드에 배치되도록 함
        """
        if self.constraint_manager is None:
            return df
        
        include_pairs = self.constraint_manager.get_include_pairs()
        if not include_pairs:
            return df
        
        result = df.copy()
        
        for person1, person2 in include_pairs:
            mask1 = result['이름'].astype(str).str.strip() == person1
            mask2 = result['이름'].astype(str).str.strip() == person2
            
            if mask1.any() and mask2.any():
                age1 = result.loc[mask1, '나이_정제'].iloc[0]
                # person2의 나이를 person1과 동일하게 조정 (같은 밴드에 배치)
                result.loc[mask2, '나이_정제'] = age1
        
        return result
    
    def _apply_exclude_constraints_global(self):
        """
        분리 제약 조건 전역 후처리: 같은 조에 있으면 안 되는 쌍을 분리
        """
        if self.constraint_manager is None or self.result_df is None:
            return
        
        exclude_pairs = self.constraint_manager.get_exclude_pairs()
        if not exclude_pairs:
            return
        
        for _ in range(50):  # 최대 50회 반복
            violations_fixed = True
            
            for person1, person2 in exclude_pairs:
                mask1 = self.result_df['이름'].astype(str).str.strip() == person1
                mask2 = self.result_df['이름'].astype(str).str.strip() == person2
                
                if not (mask1.any() and mask2.any()):
                    continue
                
                group1 = self.result_df.loc[mask1, '소그룹명'].iloc[0]
                group2 = self.result_df.loc[mask2, '소그룹명'].iloc[0]
                
                if group1 == group2:
                    # 위반! person2를 다른 그룹으로 이동
                    other_groups = self.result_df[self.result_df['소그룹명'] != group1]['소그룹명'].unique()
                    
                    if len(other_groups) > 0:
                        # 가장 인원이 적은 조로 이동
                        group_sizes = self.result_df.groupby('소그룹명').size()
                        target_group = group_sizes[group_sizes.index.isin(other_groups)].idxmin()
                        
                        # person2를 target_group으로 이동
                        self.result_df.loc[mask2, '소그룹명'] = target_group
                        violations_fixed = False
            
            if violations_fixed:
                break
    
    def _merge_small_bands(self, band_members: List[dict], threshold: int) -> List[dict]:
        """
        목표 인원의 80% 미만인 밴드를 인접 밴드와 병합합니다.
        """
        if len(band_members) <= 1:
            return band_members
        
        merged = []
        i = 0
        
        while i < len(band_members):
            current = band_members[i]
            
            # 현재 밴드가 threshold 미만이면 인접 밴드와 병합 시도
            if current['count'] < threshold:
                # 다음 밴드와 병합
                if i + 1 < len(band_members):
                    next_band = band_members[i + 1]
                    combined_members = pd.concat([current['members'], next_band['members']], ignore_index=True)
                    merged.append({
                        'band': (current['band'][0], next_band['band'][1]),
                        'members': combined_members,
                        'count': len(combined_members)
                    })
                    i += 2  # 두 밴드를 합쳤으므로 2개 건너뜀
                    continue
                # 이전 밴드와 병합 (마지막 밴드인 경우)
                elif len(merged) > 0:
                    prev_band = merged.pop()
                    combined_members = pd.concat([prev_band['members'], current['members']], ignore_index=True)
                    merged.append({
                        'band': (prev_band['band'][0], current['band'][1]),
                        'members': combined_members,
                        'count': len(combined_members)
                    })
                    i += 1
                    continue
            
            merged.append(current)
            i += 1
        
        return merged

    def _assign_leaders_to_groups(self, leaders: Set[str], num_groups: int):
        """
        리더를 각 그룹에 배정 (리더 나이에 맞는 조에 배정)
        - 리더의 나이를 확인하고, 해당 나이 밴드에 속하는 조에 배정
        - 이미 리더가 있는 조는 건너뛰고 다음으로 가까운 조에 배정
        """
        if self.result_df.empty:
            return
        
        leader_list = list(leaders)
        leader_rows = []
        for name in leader_list:
            data = self.df[self.df['이름'].astype(str).str.strip() == name]
            if len(data) > 0:
                row = data.iloc[0].to_dict()
                row['분류결과'] = '리더'
                # 나이 정보 추가
                if '나이_정제' in row:
                    row['리더나이'] = row['나이_정제']
                elif '나이' in row:
                    row['리더나이'] = pd.to_numeric(row['나이'], errors='coerce')
                else:
                    row['리더나이'] = 0
                leader_rows.append(row)
        
        # 각 조의 평균 나이 계산
        group_avg_ages = {}
        for group_name in self.result_df['소그룹명'].unique():
            group_df = self.result_df[self.result_df['소그룹명'] == group_name]
            if '나이' in group_df.columns:
                avg_age = pd.to_numeric(group_df['나이'], errors='coerce').mean()
            elif '나이_정제' in group_df.columns:
                avg_age = group_df['나이_정제'].mean()
            else:
                avg_age = 0
            group_avg_ages[group_name] = avg_age
        
        # 이미 리더가 있는 조 목록
        groups_with_leaders = set()
        if '분류결과' in self.result_df.columns:
            for group_name in self.result_df['소그룹명'].unique():
                group_df = self.result_df[self.result_df['소그룹명'] == group_name]
                if (group_df['분류결과'] == '리더').any():
                    groups_with_leaders.add(group_name)
        
        # 각 리더를 나이에 맞는 조에 배정
        for row in leader_rows:
            leader_age = row.get('리더나이', 0)
            
            # 리더가 없는 조 중에서 나이 차이가 가장 작은 조 찾기
            available_groups = [g for g in group_avg_ages.keys() if g not in groups_with_leaders]
            
            if not available_groups:
                # 모든 조에 리더가 있으면 첫 번째 조에 추가
                available_groups = list(group_avg_ages.keys())
            
            # 나이 차이가 가장 작은 조 선택
            best_group = min(available_groups, 
                           key=lambda g: abs(group_avg_ages.get(g, 0) - leader_age))
            
            row['소그룹명'] = best_group
            groups_with_leaders.add(best_group)
            
            # 리더나이 컬럼 제거 (임시 컬럼)
            if '리더나이' in row:
                del row['리더나이']
            
            # 결과 DF에 추가
            new_row_df = pd.DataFrame([row])
            self.result_df = pd.concat([new_row_df, self.result_df], ignore_index=True)
    
    def _auto_assign_leaders(self):
        """
        각 조에서 나이가 많고 출석이 좋은 사람 1명을 자동으로 리더로 선정합니다.
        이미 리더로 지정된 조는 건너뜁니다.
        """
        if self.result_df is None or len(self.result_df) == 0:
            return
        
        for group_name in self.result_df['소그룹명'].unique():
            group_mask = self.result_df['소그룹명'] == group_name
            group_df = self.result_df[group_mask]
            
            # 이미 리더가 있는 조는 건너뜀
            if (group_df['분류결과'] == '리더').any():
                continue
            
            # 케어 대상 제외하고 리더 후보 선정
            candidates = group_df[group_df['분류결과'] != '케어 대상']
            
            if len(candidates) == 0:
                # 케어 대상만 있는 경우, 그 중에서 가장 좋은 사람
                candidates = group_df
            
            # 나이_정제와 출석점수가 있는지 확인
            if '나이_정제' in candidates.columns and '출석점수' in candidates.columns:
                # 출석점수 내림차순, 나이 내림차순으로 정렬하여 첫 번째가 리더
                sorted_candidates = candidates.sort_values(
                    by=['출석점수', '나이_정제'], 
                    ascending=[False, False]
                )
            elif '나이_정제' in candidates.columns:
                sorted_candidates = candidates.sort_values('나이_정제', ascending=False)
            else:
                sorted_candidates = candidates
            
            if len(sorted_candidates) > 0:
                leader_idx = sorted_candidates.index[0]
                self.result_df.loc[leader_idx, '분류결과'] = '리더'
    

    
    def get_group_statistics(self) -> pd.DataFrame:
        """그룹별 통계를 생성합니다."""
        if self.result_df is None:
            raise ValueError("먼저 sort_into_groups()를 실행하세요.")
        
        import re
        
        temp_df = self.result_df.copy()
        temp_df['나이_숫자'] = pd.to_numeric(temp_df['나이'], errors='coerce')
        
        stats = temp_df.groupby('소그룹명').agg(
            인원수=('이름', 'count'),
            평균나이=('나이_숫자', lambda x: round(x.mean(), 1)),
            최소나이=('나이_숫자', 'min'),
            최대나이=('나이_숫자', 'max'),
            리더수=('분류결과', lambda x: (x == '리더').sum()),
            케어대상수=('분류결과', lambda x: (x == '케어 대상').sum())
        ).reset_index()
        
        # 조 이름을 숫자 기준으로 오름차순 정렬 (1조, 2조, ..., 10조)
        def extract_group_number(name):
            match = re.search(r'\d+', str(name))
            return int(match.group()) if match else 0
        
        stats['정렬키'] = stats['소그룹명'].apply(extract_group_number)
        stats = stats.sort_values('정렬키').drop(columns=['정렬키']).reset_index(drop=True)
        
        return stats
    
    def get_constraint_violations(self) -> List[str]:
        """제약 조건 위반 사항을 검사하고 반환"""
        violations = []
        
        if self.constraint_manager is None or self.result_df is None:
            return violations
        
        # 분리 조건 위반 검사
        for person1, person2 in self.constraint_manager.get_exclude_pairs():
            mask1 = self.result_df['이름'].astype(str).str.strip() == person1
            mask2 = self.result_df['이름'].astype(str).str.strip() == person2
            
            if mask1.any() and mask2.any():
                group1 = self.result_df.loc[mask1, '소그룹명'].iloc[0]
                group2 = self.result_df.loc[mask2, '소그룹명'].iloc[0]
                
                if group1 == group2:
                    violations.append(f"⚠️ 분리 위반: {person1}와 {person2}가 같은 조({group1})에 있습니다")
        
        # 포함 조건 위반 검사
        for person1, person2 in self.constraint_manager.get_include_pairs():
            mask1 = self.result_df['이름'].astype(str).str.strip() == person1
            mask2 = self.result_df['이름'].astype(str).str.strip() == person2
            
            if mask1.any() and mask2.any():
                group1 = self.result_df.loc[mask1, '소그룹명'].iloc[0]
                group2 = self.result_df.loc[mask2, '소그룹명'].iloc[0]
                
                if group1 != group2:
                    violations.append(f"⚠️ 포함 위반: {person1}와 {person2}가 다른 조에 있습니다 ({group1} vs {group2})")
        
        return violations
