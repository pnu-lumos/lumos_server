### 주의사항

-로컬 서버 형태이므로 추후 공용 서버로 변환 필요

-인프라 로직 미구현(추가되는대로 업로드 예정)

### 확인 방법

1. 레포지토리에서 zip 형태로 다운로드 받은 후 압축 해제 혹은 git clone
   <code>git clone https://github.com/pnu-lumos/lumos_test_server.git</code >
2. lumos_server 파일에서 터미널을 열고 명령어 입력 - 로컬 서버 띄우기
<pre><code>

# 가상환경 활성화

source .venv/bin/activate

# 의존성 설치

pip install -r requirements.txt

# 서버 실행

uvicorn app.main:app --reload
</code></pre> 3. 클라이언트 크롬 익스텐션 활성화 후 네이버 쇼핑 화면으로 가기(새로고침 후 실행 권장) 4. F12 -> console 누르고 success 또는 fail 등 처리 끝나면 다음과 같은 명령어 console에 입력하고 분석 확인 가능

<pre><code>
  allow pasting
  document.querySelectorAll('img, [role="image"]').forEach((el, i) => {
    const text = el.alt || el.getAttribute('aria-label');
    if (text && text.length > 5) {
      console.log(`%c[분석 텍스트 확인] %c${text}`, "color: green; font-weight: bold", "color: black");
    }
  });
</code></pre>

.env 파일 필요 시 연락주시면 확인하는대로 바로 보내겠습니다.
