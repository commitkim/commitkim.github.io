# apps/ — CLI 진입점

모든 모듈을 하나의 통합 CLI로 제어합니다.

## 명령어

```bash
# 뉴스 브리핑
python -m apps.cli run news --mode morning
python -m apps.cli run news --mode evening

# 자동매매
python -m apps.cli run trader

# 사이트 빌드 / 배포
python -m apps.cli build
python -m apps.cli deploy

# 스케줄 관리
python -m apps.cli schedule --list
python -m apps.cli schedule --install
python -m apps.cli schedule --remove

# 환경 지정
python -m apps.cli --env dev run trader

# 카카오톡 인증
python -m apps.cli setup kakao
```
