"""
테스트용 샘플 데이터 생성 스크립트
"""

import pandas as pd
import random

# 샘플 이름 목록
FIRST_NAMES = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '오', '한', '신', '서', '권']
LAST_NAMES = ['철수', '영희', '민수', '지영', '수진', '동현', '미나', '준호', '서연', '성민', 
              '혜진', '태호', '유진', '성호', '현정', '정민', '수빈', '재현', '소영', '진우']

def generate_sample_data(num_people: int = 100) -> pd.DataFrame:
    """
    샘플 교인 데이터를 생성합니다.
    
    Args:
        num_people: 생성할 인원 수
        
    Returns:
        샘플 데이터가 담긴 DataFrame
    """
    data = []
    
    for i in range(num_people):
        name = random.choice(FIRST_NAMES) + random.choice(LAST_NAMES)
        # 나이: 20~70세 사이에서 정규분포로 생성 (평균 35, 표준편차 12)
        age = max(20, min(70, int(random.gauss(35, 12))))
        # 출석현황: A(30%), B(35%), C(25%), D(10%)
        attendance = random.choices(['A', 'B', 'C', 'D'], weights=[30, 35, 25, 10])[0]
        
        data.append({
            '이름': name,
            '나이': age,
            '출석현황': attendance,
            '비고': ''
        })
    
    return pd.DataFrame(data)


if __name__ == "__main__":
    # 100명 샘플 데이터 생성
    df = generate_sample_data(100)
    
    # 엑셀로 저장
    output_path = "sample_data.xlsx"
    df.to_excel(output_path, index=False, engine='openpyxl')
    
    print(f"샘플 데이터가 생성되었습니다: {output_path}")
    print(f"총 인원: {len(df)}명")
    print("\n출석현황 분포:")
    print(df['출석현황'].value_counts())
    print("\n나이 분포:")
    print(df['나이'].describe())
