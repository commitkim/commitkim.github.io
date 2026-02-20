# MicroGPT 코드 설명 (Architecture Overview)

이 코드는 아주 작은 크기의 GPT 모델을 처음부터 끝까지 파이썬으로 직접 구현한 것입니다. 
크게 3가지 핵심 부분으로 나뉩니다: **Autograd Engine (자동 미분기)**, **Neural Network (신경망)**, **Training Loop (학습 루프)**.

---

## 1. `class Value` (Autograd Engine)
딥러닝의 핵심인 '역전파(Backpropagation)'를 수행하는 가장 기본 단위입니다.

- **역할**: 숫자 하나(`data`)를 저장하고, 이 숫자가 어떤 연산(더하기, 곱하기 등)을 통해 만들어졌는지 기억합니다.
- **주요 기능**:
    - `data`: 실제 숫자 값.
    - `grad`: 기울기(Gradient). 최종 결과(Loss)에 이 숫자가 얼마나 영향을 미쳤는지 나타냅니다.
    - `_backward()`: 자신의 기울기를 자신을 만든 부모 노드들에게 전파하는 함수입니다.
    - **예시**: `c = a + b`일 때, `c`의 기울기를 알면 `a`와 `b`의 기울기도 구할 수 있습니다.

## 2. `class MicroGPTVisualizer` (Model & Trainer)
GPT 모델의 구조 정의와 학습 과정을 총괄하는 클래스입니다.

### 모델 구조 (`_init_model`, `gpt` 메서드)
모델은 입력된 문자를 다음 문자로 예측하기 위해 다음과 같은 단계를 거칩니다:

1.  **Embedding (임베딩)**:
    - `wte` (Token Embedding): 각 글자(a, b, c...)를 고유한 벡터(숫자들의 리스트)로 변환합니다.
    - `wpe` (Position Embedding): 글자의 순서(첫 번째, 두 번째...) 정보를 더해줍니다.
    
2.  **Transformer Block (트랜스포머 블록)**:
    - **Self-Attention (`attn_wq, wk, wv, wo`)**: 문맥을 파악합니다. 예: "사과를 먹었다"에서 "먹었다"가 "사과"와 관련 깊다는 것을 찾아냅니다.
    - **Feed Forward (`mlp_fc1, fc2`)**: 파악한 문맥 정보를 바탕으로 데이터를 가공하고 복잡한 특징을 추출합니다.
    
3.  **Output Head (`lm_head`)**:
    - 최종적으로 다음에 올 글자가 무엇일지 점수(logits)를 매깁니다.

### 학습 과정 (`run` 메서드)
1.  **Forward Pass (순전파)**: 데이터를 모델에 넣어 예측값을 뽑고, 정답과 비교해 오차(Loss)를 구합니다.
2.  **Backward Pass (역전파)**: `loss.backward()`를 호출하여 오차를 줄이기 위해 각 파라미터를 어떻게 조절해야 할지(Gradient) 계산합니다.
3.  **Update (업데이트)**: 계산된 Gradient를 바탕으로 파라미터를 아주 조금 수정합니다(Learning Rate). 이 과정을 반복하면 모델이 점점 똑똑해집니다.

---

## 3. 시각화 데이터 생성
이 코드는 학습만 하는 것이 아니라, 학습 과정에서 발생하는 모든 데이터(Loss 변화, 연산 그래프 등)를 `data/microgpt/trace.json`에 저장합니다. 이 데이터가 웹 페이지에서 시각화되어 보여집니다.
