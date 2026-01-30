# CHANGELOG (변경 이력)

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
