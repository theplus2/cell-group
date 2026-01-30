# Handoff (현재 상태)

## 📌 현재 상태
- **현재 버전**: v2.9
- **빌드 상태**: 🔄 진행 중 (GitHub Actions)
- **주요 URL**: [GitHub Releases](https://github.com/theplus2/cell-group/releases)

## 🚀 최근 작업 요약
1. **PySide6 마이그레이션 (v2.9)**: PyQt6에서 Qt Company 공식 바인딩인 PySide6로 변경하여 Smart App Control 호환성 개선.
2. **보안 정책 우회 (v2.8.3)**: 설치 경로를 `LocalAppData`로 변경하고 관리자 권한 요구 제거.

## ⚠️ 알려진 이슈
- 사용자 PC의 Smart App Control이 **"평가 모드"** 이상으로 활성화되어 있어 서명되지 않은 모든 실행 파일/DLL 차단 중.
- PySide6가 더 나은 서명 상태를 가지므로 개선이 예상되나, 완전한 해결은 코드 서명 인증서 구매가 필요할 수 있음.

## 📝 TODO
1. v2.9 빌드 결과 확인 및 사용자 테스트
2. 여전히 차단될 경우 사용자에게 Smart App Control 예외 처리 또는 비활성화 안내
3. (장기) 유료 코드 서명 인증서 도입 검토

