"""
교인 소그룹 자동 편성 시스템 (Small Group Sorter)
메인 실행 파일
"""

import argparse
from pathlib import Path

from src.data_loader import DataLoader
from src.preprocessor import DataPreprocessor
from src.sorter import GroupSorter
from src.config import SorterConfig, DEFAULT_CONFIG


def main(input_file: str, output_file: str = None, config: SorterConfig = None):
    """
    메인 실행 함수
    
    Args:
        input_file: 입력 엑셀/CSV 파일 경로
        output_file: 출력 파일 경로 (선택, 기본값: sorted_result.xlsx)
        config: 편성 설정 (선택, 기본값 사용)
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    if output_file is None:
        output_file = config.output_filename
    
    print("=" * 50)
    print("교인 소그룹 자동 편성 시스템")
    print("=" * 50)
    
    # 1. 데이터 로드
    print(f"\n[1/4] 데이터 로드 중: {input_file}")
    loader = DataLoader()
    df = loader.load_file(input_file)
    print(f"  → {len(df)}명의 교인 데이터를 로드했습니다.")
    
    # 2. 컬럼 검증
    is_valid, missing = loader.validate_columns()
    if not is_valid:
        print(f"  ⚠️  누락된 필수 컬럼: {missing}")
        print("  파일에 '이름', '나이', '출석현황' 컬럼이 필요합니다.")
        return
    print("  → 필수 컬럼 검증 완료")
    
    # 3. 데이터 전처리
    print("\n[2/4] 데이터 전처리 중...")
    preprocessor = DataPreprocessor(df)
    processed_df = preprocessor.process()
    print("  → 나이 정제, 출석점수 변환, 역할 분류 완료")
    
    # 4. 소그룹 편성
    print(f"\n[3/4] 소그룹 편성 중 (그룹당 {config.group_size}명, 나이차 ±{config.age_tolerance}살)...")
    sorter = GroupSorter(
        processed_df,
        group_size=config.group_size,
        age_tolerance=config.age_tolerance
    )
    result_df = sorter.sort_into_groups()
    stats_df = sorter.get_group_statistics()
    
    num_groups = result_df['소그룹명'].nunique()
    print(f"  → 총 {num_groups}개의 소그룹으로 편성 완료")
    
    # 5. 결과 저장
    print(f"\n[4/4] 결과 저장 중: {output_file}")
    loader.save_result(result_df, output_file, stats_df)
    
    # 6. 통계 출력
    print("\n" + "=" * 50)
    print("📊 그룹별 통계 요약")
    print("=" * 50)
    print(stats_df.to_string(index=False))
    
    print("\n✅ 소그룹 편성이 완료되었습니다!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="교인 소그룹 자동 편성 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py raw_data.xlsx
  python main.py raw_data.xlsx -o result.xlsx
  python main.py raw_data.xlsx --group-size 8 --age-tolerance 7
        """
    )
    
    parser.add_argument(
        "input_file",
        help="입력 파일 경로 (.xlsx 또는 .csv)"
    )
    parser.add_argument(
        "-o", "--output",
        default="sorted_result.xlsx",
        help="출력 파일 경로 (기본값: sorted_result.xlsx)"
    )
    parser.add_argument(
        "-g", "--group-size",
        type=int,
        default=10,
        help="그룹당 목표 인원 (기본값: 10)"
    )
    parser.add_argument(
        "-a", "--age-tolerance",
        type=int,
        default=5,
        help="그룹 내 허용 나이 차이 ±N살 (기본값: 5)"
    )
    
    args = parser.parse_args()
    
    config = SorterConfig(
        group_size=args.group_size,
        age_tolerance=args.age_tolerance,
        output_filename=args.output
    )
    
    main(args.input_file, args.output, config)
