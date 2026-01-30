# CHANGELOG (변경 이력)

## [v3.0.0] - 2026-01-30
### Added
- **초기화 버튼**: GUI 상단에 데이터를 초기화할 수 있는 버튼 추가.
- **나이 범위 시각화**: 그룹 내 나이 차이가 10살을 초과하면 노란색 경고 표시.
- **버전 정보 중앙화**: `src/config.py`를 통해 버전 정보 일원화.

### Changed
- **멤버 정렬**: 그룹 내 멤버 정렬 순서를 `리더 → 출석점수(성적) 순`으로 변경.
- **빌드**: GitHub Actions 워크플로우를 태그 기반 자동 릴리즈로 최적화.

## [v2.9.1] - 2026-01-30
### Fixed
- `gui_app.py`: `pyqtSignal`을 `Signal`로 수정하여 실행 오류 해결.

## [v2.9] - 2026-01-30
### Changed
- `requirements.txt`: PyQt6를 PySide6로 변경 (Qt Company 공식 바인딩으로 Smart App Control 호환성 향상)
- `gui_app.py`: 모든 PyQt6 import를 PySide6로 마이그레이션, `pyqtSignal` → `Signal` 변경.

## [v2.8.3] - 2026-01-30
### Added

- `setup.iss`: `PrivilegesRequired=lowest` 추가 (관리자 권한 없이 설치 가능)

### Changed
- `setup.iss`: 설치 경로를 `{autopf}`에서 `{localappdata}\SmallGroupSorter`로 변경. (보안 정책에 의한 DLL 차단 방지)
- `file_version_info.txt`: 버전을 2.8.3으로 업데이트.

## [v2.8.2] - 2026-01-30
### Added
- `file_version_info.txt`: 실행 파일 메타데이터(회사명, 제품명, 서술자, 저작권자) 추가.
- `.github/workflows/release.yml`: PyInstaller 빌드 시 `--noupx` 옵션 및 `--version-file` 추가.

### Changed
- `setup.iss`: 앱 이름 및 발행자 정보를 '소그룹 자동 편성기', '잠실한빛교회 (윤영천 목사)'로 변경.

## [v2.8.1] - 2026-01-30
### Fixed
- `setup.iss`: Inno Setup에서 지원하지 않는 `.png` 아이콘 설정 제거.

## [v2.8.0] - 2026-01-30
### Added
- `gui_app.py`: 제약 조건 탭의 이름 입력창에 자동 완성(`QCompleter`) 기능 추가.
- `src/sorter.py`: 리더 1조 1명 강제 배정 및 나이 중앙값/범위 기반 매칭 알고리즘 개선.

## [v2.7.1] - 2026-01-23
### Fixed
- `requirements.txt`: PyInstaller 스플래시 이미지 처리를 위한 `Pillow` 라이브러리 추가.

## [v2.7.0] - 2026-01-23
### Added
- 로딩 속도 개선을 위한 스플래시 화면(`pyi_splash`) 도입.
- 하이브리드 빌드 파이프라인 (Portable EXE + Setup Installer).
