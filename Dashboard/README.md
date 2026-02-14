# Dashboard Hub 📊

**CommitKim 프로젝트의 중앙 관제탑**
*This project is generated and maintained by Google's Agentic AI.*

---

## 📝 개요
이 대시보드는 `Summariser`가 수집한 경제 뉴스 데이터와 `Slot Machine` 게임 등 다양한 프로젝트를 한눈에 볼 수 있는 정적 웹사이트입니다.

## ⚙️ 주요 기능
1.  **듀얼 뉴스 아카이브**: 매일 오전/오후 생성되는 경제 뉴스 요약본을 탭 형식의 UI로 제공합니다.
    - `data/news/morning/` 및 `data/news/evening/` 데이터를 기반으로 상세 페이지를 자동 생성합니다.
2.  **슬롯 머신 연동**: '다이어트 심판대' 게임으로 바로 이동할 수 있습니다.
3.  **반응형 및 정제된 UI**: TailwindCSS 기반의 정제된 디자인과 단일 컬럼 리스트로 가독성을 극대화했습니다.

## 🛠️ 기술 스택
- **Generator**: Python 3.12+ (Custom Builder)
- **Templating**: Jinja2
- **Styling**: TailwindCSS (CDN)
- **Hosting**: GitHub Pages

## 🏗️ 빌드 프로세스
```bash
python builder.py
```
위 명령어를 실행하면 `templates/` 폴더의 HTML 템플릿과 `data/` 폴더의 JSON 데이터를 결합하여 `../docs/` 폴더에 최종 정적 사이트를 생성합니다.

## 🧪 테스트
- **빌드 테스트**: 임시 폴더에서 사이트 생성을 검증합니다.
    ```bash
    ..\tests\test_dashboard.bat
    ```
