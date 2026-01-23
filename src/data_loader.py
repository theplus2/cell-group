"""
데이터 입출력 모듈
- 엑셀/CSV 파일 로드
- 필수 컬럼 검증
- 제약 조건 시트 로드
- 결과 파일 생성
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .constraints import ConstraintManager


class DataLoader:
    """엑셀 및 CSV 데이터 로드/저장 클래스"""
    
    REQUIRED_COLUMNS = ['이름', '나이', '출석현황']
    CONSTRAINT_SHEET_NAME = '제약조건'
    
    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.file_path: Optional[Path] = None
        self.constraint_df: Optional[pd.DataFrame] = None
    
    def load_file(self, file_path: str) -> pd.DataFrame:
        """
        엑셀 또는 CSV 파일을 로드합니다.
        
        Args:
            file_path: 로드할 파일 경로 (.xlsx 또는 .csv)
            
        Returns:
            로드된 DataFrame
            
        Raises:
            ValueError: 지원하지 않는 파일 형식
            FileNotFoundError: 파일을 찾을 수 없음
        """
        self.file_path = Path(file_path)
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        suffix = self.file_path.suffix.lower()
        
        if suffix == '.xlsx':
            self.data = pd.read_excel(file_path, engine='openpyxl')
            # 제약조건 시트 로드 시도
            self._load_constraint_sheet(file_path)
        elif suffix == '.csv':
            self.data = pd.read_csv(file_path, encoding='utf-8-sig')
            self.constraint_df = None  # CSV는 제약조건 시트 없음
        else:
            raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")
        
        return self.data
    
    def _load_constraint_sheet(self, file_path: str):
        """제약조건 시트 로드 (존재하는 경우)"""
        try:
            xl = pd.ExcelFile(file_path, engine='openpyxl')
            if self.CONSTRAINT_SHEET_NAME in xl.sheet_names:
                self.constraint_df = pd.read_excel(
                    xl, 
                    sheet_name=self.CONSTRAINT_SHEET_NAME
                )
            else:
                self.constraint_df = None
        except Exception:
            self.constraint_df = None
    
    def get_names(self) -> Set[str]:
        """로드된 데이터에서 이름 목록 추출"""
        if self.data is None or '이름' not in self.data.columns:
            return set()
        return set(self.data['이름'].dropna().astype(str).str.strip())
    
    def get_constraint_manager(self) -> 'ConstraintManager':
        """제약조건 DataFrame을 ConstraintManager로 변환"""
        from .constraints import ConstraintManager
        return ConstraintManager.from_dataframe(self.constraint_df)
    
    def has_constraints(self) -> bool:
        """제약조건 시트가 있는지 확인"""
        return self.constraint_df is not None and not self.constraint_df.empty
    
    def validate_columns(self) -> Tuple[bool, list]:
        """
        필수 컬럼이 존재하는지 검증합니다.
        
        Returns:
            (검증 성공 여부, 누락된 컬럼 목록)
        """
        if self.data is None:
            return False, self.REQUIRED_COLUMNS
        
        missing = [col for col in self.REQUIRED_COLUMNS if col not in self.data.columns]
        return len(missing) == 0, missing
    
    def save_result(
        self, 
        df: pd.DataFrame, 
        output_path: str, 
        summary_df: Optional[pd.DataFrame] = None,
        constraint_manager: Optional['ConstraintManager'] = None
    ):
        """
        결과를 엑셀 파일로 저장합니다.
        GUI와 동일한 조별 가로 편성표 형식으로 출력합니다.
        
        Args:
            df: 저장할 메인 데이터프레임
            output_path: 출력 파일 경로
            summary_df: 그룹별 통계 요약 데이터프레임 (선택)
            constraint_manager: 제약 조건 관리자 (선택)
        """
        import re
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 조별 가로 편성표 형식으로 변환
            if '소그룹명' in df.columns:
                # 조 이름을 숫자 기준 오름차순 정렬
                def extract_group_number(name):
                    match = re.search(r'\d+', str(name))
                    return int(match.group()) if match else 0
                
                groups = df.groupby('소그룹명')
                group_names = sorted(groups.groups.keys(), key=extract_group_number)
                
                # 가장 많은 인원이 있는 조의 멤버 수 계산
                max_members = max(len(groups.get_group(g)) for g in group_names)
                
                # 조별 편성표 데이터 생성
                rows = []
                for group_name in group_names:
                    group_df = groups.get_group(group_name).copy()
                    
                    # 리더→일반→케어 대상 순으로 정렬
                    sort_order = {'리더': 0, '일반': 1, '케어 대상': 2}
                    if '분류결과' in group_df.columns:
                        group_df['정렬순서'] = group_df['분류결과'].map(lambda x: sort_order.get(x, 1))
                        group_df = group_df.sort_values('정렬순서')
                    
                    # 멤버 이름 추출 (리더는 ⭐ 표시)
                    members = []
                    for _, member in group_df.iterrows():
                        name = str(member.get('이름', ''))
                        분류 = member.get('분류결과', '')
                        if 분류 == '리더':
                            members.append(f"⭐ {name}")
                        else:
                            members.append(name)
                    
                    # 빈 셀 채우기
                    while len(members) < max_members:
                        members.append('')
                    
                    rows.append([group_name] + members)
                
                # 헤더 설정
                headers = ['조'] + [f'멤버 {i+1}' for i in range(max_members)]
                result_df = pd.DataFrame(rows, columns=headers)
                result_df.to_excel(writer, sheet_name='소그룹 편성 결과', index=False)
            else:
                df.to_excel(writer, sheet_name='소그룹 편성 결과', index=False)
            
            if summary_df is not None:
                summary_df.to_excel(writer, sheet_name='그룹별 통계', index=False)
            
            if constraint_manager is not None and len(constraint_manager) > 0:
                constraint_df = constraint_manager.to_dataframe()
                constraint_df.to_excel(
                    writer, 
                    sheet_name=self.CONSTRAINT_SHEET_NAME, 
                    index=False
                )
        
        print(f"결과가 저장되었습니다: {output_path}")

