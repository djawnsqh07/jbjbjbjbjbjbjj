import streamlit as st
import datetime
import sqlite3
import hashlib # 비밀번호 해싱을 위한 라이브러리

# --- 0. SQLite 데이터베이스 설정 ---
DB_NAME = 'users.db' # 데이터베이스 파일 이름

def init_db():
    """데이터베이스를 초기화하고 users 테이블을 생성합니다."""
    print("DEBUG: init_db() 함수 시작.") # 디버그 출력
    conn = None # conn을 None으로 초기화
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        print(f"DEBUG: 데이터베이스에 연결 시도: {DB_NAME}") # 디버그 출력
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                email TEXT,
                gender TEXT,
                birthday TEXT,
                age INTEGER
            )
        ''')
        conn.commit()
        print("DEBUG: users 테이블이 생성/확인됨.") # 디버그 출력
    except sqlite3.Error as e: # SQLite 관련 특정 오류 잡기
        print(f"ERROR: init_db 중 SQLite 오류 발생: {e}")
    except Exception as e: # 그 외 예상치 못한 모든 오류 잡기
        print(f"ERROR: init_db 중 일반 오류 발생: {e}")
    finally:
        if conn: # 연결이 열려있다면 닫기
            conn.close()
            print("DEBUG: 데이터베이스 연결 종료.") # 디버그 출력

# 앱 시작 시 데이터베이스 초기화 함수 호출
print("DEBUG: 앱 시작 시 init_db() 호출 중.") # 디버그 출력
init_db()

def hash_password(password):
    """비밀번호를 SHA256으로 해싱합니다. 보안 강화를 위해 사용합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- 1. 세션 상태 관리 ---
# 웹사이트 새로고침 시에도 유지될 상태 변수들
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = "로그인" # 초기 페이지 설정

# 추가: 문제점 목록을 저장할 리스트 (앱 재시작 시 초기화됨, 영구 저장을 원하면 DB 필요)
if 'issues' not in st.session_state:
    st.session_state.issues = []

# --- 2. 사용자 인증 및 등록 함수 ---
def authenticate_user(username, password):
    """
    데이터베이스에서 사용자 인증을 시도합니다.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_password = hash_password(password) # 입력받은 비밀번호도 해싱
    # 데이터베이스에서 아이디와 해싱된 비밀번호가 일치하는 사용자 조회
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone() # 일치하는 사용자 정보 가져오기 (없으면 None)
    conn.close()

    if user: # 사용자 정보가 있으면 로그인 성공
        st.session_state.logged_in = True
        st.session_state.username = user[0] # 데이터베이스에서 가져온 사용자 이름 설정
        st.session_state.page = "문제점 접수" # 로그인 성공 시 이동 페이지
        st.success(f"**{username}**님 환영합니다!")
        st.balloons() # 풍선 효과
        st.rerun() # UI 업데이트를 위해 Streamlit 앱 새로고침
    else: # 사용자 정보가 없으면 로그인 실패
        st.error("로그인 실패: 아이디 또는 비밀번호를 확인해주세요.")
        st.session_state.logged_in = False

def register_user(username, password, email, gender, birthday, age):
    """
    새로운 사용자를 데이터베이스에 등록합니다.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        hashed_password = hash_password(password) # 비밀번호 해싱하여 저장
        # --- 디버깅용 print ---
        print(f"DEBUG: register_user 함수 호출됨. 사용자명: {username}, 해싱된 비밀번호(일부): {hashed_password[:10]}...")
        # -------------------
        c.execute("INSERT INTO users (username, password, email, gender, birthday, age) VALUES (?, ?, ?, ?, ?, ?)",
                  (username, hashed_password, email, gender, birthday, age))
        conn.commit() # 변경사항 저장
        conn.close()
        # --- 디버깅용 print ---
        print(f"DEBUG: 사용자 {username} 데이터베이스에 성공적으로 등록됨.")
        # -------------------
        return True # 등록 성공
    except sqlite3.IntegrityError: # PRIMARY KEY (username) 충돌 시 (이미 존재하는 아이디)
        conn.close()
        # --- 디버깅용 print ---
        print(f"DEBUG: 사용자 {username} 등록 실패 - 이미 존재하는 아이디.")
        # -------------------
        return False # 등록 실패 (아이디 중복)
    except Exception as e: # 다른 종류의 예외도 잡아서 확인
        conn.close()
        # --- 디버깅용 print ---
        print(f"DEBUG: 사용자 {username} 등록 중 예상치 못한 오류 발생: {e}")
        # -------------------
        return False


# --- 3. UI 레이아웃 및 페이지 라우팅 ---
st.sidebar.title("학교 문제점 시스템")

# 사이드바 메뉴 구성: 로그인 여부에 따라 다르게 표시
if not st.session_state.logged_in:
    selected_menu = st.sidebar.selectbox("메뉴", ["로그인", "회원가입"])
    # 사이드바 선택에 따라 st.session_state.page를 명시적으로 업데이트
    if st.session_state.page != selected_menu: # 현재 페이지와 선택 메뉴가 다르면
        st.session_state.page = selected_menu # 페이지 상태를 업데이트
        st.rerun() # 즉시 페이지 전환을 위해 새로고침

    # --- 디버깅용 print ---
    print(f"DEBUG: 로그인되지 않음. selected_menu: {selected_menu}, st.session_state.page: {st.session_state.page}")
    # -------------------
else:
    selected_menu = st.sidebar.selectbox("메뉴", ["문제점 접수", "내 문제점 보기", "로그아웃"])
    # 사이드바 선택에 따라 st.session_state.page를 명시적으로 업데이트
    if st.session_state.page != selected_menu: # 현재 페이지와 선택 메뉴가 다르면
        st.session_state.page = selected_menu # 페이지 상태를 업데이트
        st.rerun() # 즉시 페이지 전환을 위해 새로고침

    st.sidebar.write(f"환영합니다, **{st.session_state.username}**님!")
    # --- 디버깅용 print ---
    print(f"DEBUG: {st.session_state.username}으로 로그인됨. selected_menu: {selected_menu}, st.session_state.page: {st.session_state.page}")
    # -------------------

    # 로그아웃 버튼 클릭 시 세션 상태 초기화
    if selected_menu == "로그아웃": # 'menu' 대신 'selected_menu' 사용
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.page = "로그인" # 로그아웃 후 로그인 페이지로 이동
        st.info("로그아웃 되었습니다.")
        # --- 디버깅용 print ---
        print("DEBUG: 로그아웃됨. 새로고침 중.")
        # -------------------
        st.rerun()

# --- 4. 각 메뉴 선택에 따른 페이지 내용 표시 ---
# 이제 'st.session_state.page' 값만으로 페이지를 라우팅합니다.

# 로그인 페이지
if st.session_state.page == "로그인":
    st.title("로그인")
    # --- 디버깅용 print ---
    print("DEBUG: 로그인 페이지 표시 중.")
    # -------------------
    username = st.text_input("아이디", key="login_username_input")
    password = st.text_input("비밀번호", type="password", key="login_password_input")
    login_button = st.button("로그인")

    if login_button:
        # --- 디버깅용 print ---
        print(f"DEBUG: '{username}'로 로그인 버튼 클릭됨.")
        # -------------------
        authenticate_user(username, password) # SQLite 기반 인증 함수 호출

# 회원가입 페이지
elif st.session_state.page == "회원가입":
    st.title("회원가입")
    # --- 디버깅용 print ---
    print("DEBUG: 회원가입 페이지 표시 중.")
    # -------------------
    with st.form("signup_form"): # Streamlit의 폼 기능을 사용하여 입력 필드를 그룹화
        new_username = st.text_input("아이디", key="signup_username_input")
        new_password = st.text_input("비밀번호", type="password", key="signup_password_input")
        new_password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm_input")
        new_email = st.text_input("이메일", key="signup_email_input")
        new_gender = st.selectbox("성별", ["선택 안 함", "남성", "여성", "기타"], key="signup_gender_select")
        # datetime 모듈을 사용하여 날짜 입력 필드 제공, DB 저장을 위해 문자열로 변환
        new_birthday = st.date_input("생일", datetime.date(2000, 1, 1), key="signup_birthday_input").strftime("%Y-%m-%d")
        new_age = st.number_input("나이", min_value=0, max_value=150, step=1, key="signup_age_input")

        join_button = st.form_submit_button("회원가입")

        if join_button:
            # --- 디버깅용 print ---
            print("DEBUG: 회원가입 폼 제출됨.")
            # -------------------
            if not new_username or not new_password or not new_password_confirm:
                st.error("아이디, 비밀번호, 비밀번호 확인은 필수 입력 항목입니다.")
                # --- 디버깅용 print ---
                print("DEBUG: 회원가입: 필수 필드 누락.")
                # -------------------
            elif new_password != new_password_confirm:
                st.error("비밀번호와 비밀번호 확인이 일치하지 않습니다.")
                # --- 디버깅용 print ---
                print("DEBUG: 회원가입: 비밀번호 불일치.")
                # -------------------
            else:
                # register_user 함수를 호출하여 데이터베이스에 사용자 정보 저장
                if register_user(new_username, new_password, new_email, new_gender, new_birthday, new_age):
                    st.success(f"**{new_username}**님, 회원가입이 완료되었습니다! 이제 로그인할 수 있습니다.")
                    st.session_state.page = "로그인" # 회원가입 성공 시 로그인 페이지로 이동
                    # --- 디버깅용 print ---
                    print(f"DEBUG: 회원가입: {new_username} 등록됨. 로그인 페이지로 새로고침 중.")
                    # -------------------
                    st.rerun() # UI 업데이트를 위해 새로고침
                else:
                    st.error("이미 존재하는 아이디입니다. 다른 아이디를 사용해주세요.")
                    # --- 디버깅용 print ---
                    print(f"DEBUG: 회원가입: {new_username} 이미 존재하거나 등록 실패.")
                    # -------------------

# 문제점 접수 페이지 (로그인한 사용자만 접근 가능)
elif st.session_state.page == "문제점 접수":
    st.title("문제점 접수")
    # --- 디버깅용 print ---
    print("DEBUG: 문제점 접수 페이지 표시 중.")
    # -------------------
    st.write(f"환영합니다, **{st.session_state.username}**님! 어떤 문제점을 접수하시겠어요?")

    with st.form("issue_submission_form"):
        issue_title = st.text_input("문제점 제목", max_chars=100, key="issue_title_input")
        issue_type = st.selectbox("문제점 종류", ["시설", "학사", "교우 관계", "건의 사항", "기타"], key="issue_type_select")
        issue_description = st.text_area("문제점 상세 내용", height=200, key="issue_description_input")

        # 문제점 접수 날짜 자동 생성 (오늘 날짜)
        submission_date = datetime.date.today().strftime("%Y년 %m월 %d일")
        st.markdown(f"**접수 날짜:** {submission_date}") # 사용자에게 표시

        submit_issue_button = st.form_submit_button("문제점 접수하기")

        if submit_issue_button:
            # --- 디버깅용 print ---
            print("DEBUG: 문제점 접수 폼 제출됨.")
            # -------------------
            if not issue_title or not issue_description:
                st.warning("제목과 상세 내용은 필수 입력 사항입니다.")
                # --- 디버깅용 print ---
                print("DEBUG: 문제점 접수: 필수 필드 누락.")
                # -------------------
            else:
                st.success("문제점이 성공적으로 접수되었습니다!")
                st.info(f"**제목:** {issue_title}\n**종류:** {issue_type}\n**내용:** {issue_description}")

                # 접수된 문제점을 세션 상태에 저장 (앱 재시작 시 초기화됨)
                new_issue = {
                    "제목": issue_title,
                    "종류": issue_type,
                    "내용": issue_description,
                    "접수자": st.session_state.username, # 현재 로그인한 사용자 이름 기록
                    "접수일": submission_date
                }
                st.session_state.issues.append(new_issue)
                # --- 디버깅용 print ---
                print(f"DEBUG: 문제점 접수됨: {issue_title}. 총 문제점 수: {len(st.session_state.issues)}")
                # -------------------

                st.session_state.page = "내 문제점 보기" # 접수 완료 후 자동으로 내 문제점 보기 페이지로 이동
                st.rerun() # UI 업데이트를 위해 새로고침

# 내 문제점 보기 페이지
elif st.session_state.page == "내 문제점 보기":
    st.title("내 문제점 보기")
    # --- 디버깅용 print ---
    print("DEBUG: 내 문제점 보기 페이지 표시 중.")
    # -------------------

    # 현재 로그인한 사용자가 접수한 문제점만 필터링하여 보여줌
    user_issues = [issue for issue in st.session_state.issues if issue.get("접수자") == st.session_state.username]

    if user_issues: # 필터링된 문제점이 있으면 목록 표시
        st.write(f"**{st.session_state.username}**님이 접수한 문제점 목록입니다:")

        # 각 문제점을 확장 가능한 형태로 표시
        for i, issue in enumerate(user_issues):
            with st.expander(f"**{issue['제목']}** (종류: {issue['종류']}, 접수일: {issue['접수일']})"):
                st.write(f"**내용:** {issue['내용']}")
                # 필요하다면 여기에 추가 정보 (예: 접수자)를 표시할 수 있습니다.
    else: # 접수된 문제점이 없으면 안내 메시지 표시
        st.info("아직 접수하신 문제점이 없습니다.")
        st.info("좌측 메뉴에서 '문제점 접수'를 통해 새로운 문제점을 접수해보세요.")