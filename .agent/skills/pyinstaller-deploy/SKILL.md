---
name: pyinstaller-git-deploy
description: PyInstaller를 이용한 EXE 빌드와 Git 버전 태깅 및 푸시 과정을 자동화합니다. "빌드해서 배포해줘", "태그 달아서 올려줘"라고 할 때 사용합니다.
---

# 목표
Python GUI 앱을 빌드하고, 버전을 매겨 저장소에 안전하게 배포합니다.

# 지침

## 1. EXE 빌드 (PyInstaller)
- 다음 명령어를 사용하여 단일 파일 실행 파일을 생성합니다:
  ```powershell
  python -m PyInstaller --onefile --windowed --name [앱이름] gui_app.py
  ```
- 빌드 완료 후 `dist/` 폴더 내에 생성된 파일을 확인합니다.

## 2. Git 버전 관리 및 태깅
- **변경 사항 확인:** `git status`로 누락된 파일이 있는지 확인합니다.
- **커밋:** `feat: vX.X 배포` 형식으로 커밋합니다.
- **태그 생성:** 기존 태그와 겹치지 않게 버전을 지정합니다. (예: `v2.5`)
  ```powershell
  git tag v[버전]
  ```
- **원격 푸시:** 브랜치와 태그를 모두 푸시합니다.
  ```powershell
  git push origin main
  git push origin v[버전]
  ```

## 3. 체크리스트
- `.gitignore`에 `dist/`, `build/`, `*.spec`이 포함되어 있는지 확인하세요.
- 원격 저장소(`origin`)가 제대로 연결되어 있는지 확인하세요.
- 빌드 중 에러가 발생하면 `requirements.txt`의 의존성을 다시 확인하세요.

# 제약 사항
- 이미 존재하는 태그를 덮어쓰지 않도록 주의하세요.
- 빌드 결과물(dist 폴더)은 저장소에 올리지 않는 것이 원칙입니다.
