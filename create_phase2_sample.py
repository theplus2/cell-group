"""
Phase 2 제약 조건 테스트용 샘플 데이터 생성 스크립트
"""

import pandas as pd
import random
import os

# 샘플 이름 데이터
NAMES = [f"교인{i}" for i in range(1, 51)]  # 50명

def generate_data_with_constraints():
    # 1. 교인 명단 데이터 생성
    data = []
    for name in NAMES:
        age = random.randint(20, 60)
        attendance = random.choice(['A', 'B', 'C', 'D'])
        data.append({
            '이름': name,
            '나이': age,
            '출석현황': attendance
        })
    
    df = pd.DataFrame(data)
    
    # 2. 제약 조건 데이터 생성
    constraints = [
        # 리더 지정 (2명)
        {'유형': '리더', '대상1': '교인1', '대상2': '', '메모': '1조 리더'},
        {'유형': '리더', '대상1': '교인20', '대상2': '', '메모': '2조 리더'},
        
        # 포함 조건 (부부/커플)
        {'유형': '포함', '대상1': '교인2', '대상2': '교인3', '메모': '부부'},
        {'유형': '포함', '대상1': '교인10', '대상2': '교인11', '메모': '자매'},
        {'유형': '포함', '대상1': '교인30', '대상2': '교인31', '메모': '친구'},
        
        # 분리 조건 (갈등)
        {'유형': '분리', '대상1': '교인5', '대상2': '교인6', '메모': '성격 차이'},
        {'유형': '분리', '대상1': '교인40', '대상2': '교인41', '메모': '과거 다툼'},
    ]
    
    constraints_df = pd.DataFrame(constraints)
    
    # 3. 엑셀 파일로 저장 (시트 구분)
    output_path = "sample_with_constraints.xlsx"
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='교인명단', index=False)
        constraints_df.to_excel(writer, sheet_name='제약조건', index=False)
        
    print(f"제약 조건 샘플 데이터가 생성되었습니다: {output_path}")
    print(f"- 교인 수: {len(df)}명")
    print(f"- 제약 조건 수: {len(constraints_df)}개")
    print("\n제약 조건 미리보기:")
    print(constraints_df)

if __name__ == "__main__":
    generate_data_with_constraints()
