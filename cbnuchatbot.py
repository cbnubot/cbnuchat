# -*- coding: utf-8 -*-
"""
CBNU 챗봇
- SQLite 기반 자원 검색 (키워드를 치면 바로 브라우저 열림)
- CLI 및 GUI 모드 지원
- 한/영 다국어 토글 기능 포함

아래 initial_data 항목 중 “실행 확인된” URL만 포함되어 있으며,
더 이상 동작하지 않는 링크는 모두 제거하였습니다.
"""
import sqlite3
import webbrowser
import os
import difflib
import tkinter as tk
from typing import List, Tuple

# ------------------------------------------------------------------
# 설정 및 다국어 메시지
# ------------------------------------------------------------------
DB_FILE = 'cbnu_bot.db'               # DB 파일 이름
HISTORY_FILE = 'search_history.txt'   # 검색 기록 파일 이름
LANG = 'ko'                           # 기본 언어: 'ko' 또는 'en'

# 다국어 메시지 사전
messages = {
    'welcome': {
        'ko': '충북대 챗봇에 오신 것을 환영합니다!',
        'en': 'Welcome to CBNU Bot!'
    },
    'help': {
        'ko': '검색 가능한 키워드 목록을 보려면 help를 입력하세요.',
        'en': 'Type help to see available search keywords.'
    },
    'search_label': {
        'ko': '검색어 입력:',
        'en': 'Enter keyword:'
    },
    'search_button': {
        'ko': '검색',
        'en': 'Search'
    },
    'lang_button': {
        'ko': 'English',
        'en': '한국어'
    },
    'suggest': {
        'ko': '혹시 다음 키워드를 찾으시나요?',
        'en': 'Did you mean:'
    },
    'exit_msg': {
        'ko': '안녕히 가세요!',
        'en': 'Goodbye!'
    }
}

def get_msg(key: str) -> str:
    """
    다국어 메시지를 반환
    """
    return messages.get(key, {}).get(LANG, '')

# ------------------------------------------------------------------
# “초기 데이터”를 전역 변수로 꺼내 둠
# (동작이 확인된 URL만 남겨두었습니다.)
# ------------------------------------------------------------------
initial_data = [
    ('장학금',       'https://www.cbnu.ac.kr/www/contents.do?key=492'),
    ('학사일정',     'https://www.cbnu.ac.kr/www/selectWebSchdulList.do?key=455&schdulSeNo=1'),
    ('수강신청',     'https://eisa.cbnu.ac.kr/'),
    ('도서관',       'https://cbnul.chungbuk.ac.kr/'),
    ('셔틀버스',     'https://www.cbnu.ac.kr/www/contents.do?key=648'),
    ('기숙사',       'https://cia.cbnu.ac.kr/'),
    ('취업지원',     'https://hrd.cbnu.ac.kr/'),
    ('등록금',       'https://www.cbnu.ac.kr/www/contents.do?key=483'),
    ('캠퍼스맵',     'https://www.cbnu.ac.kr/www/contents.do?key=4'),
    ('씨앗시스템',   'https://seet.cbnu.ac.kr/'),
    ('LMS',         'https://lms.cbnu.ac.kr/'),
    ('마이페이지',   'https://portal.cbnu.ac.kr/'),
   
]

# ------------------------------------------------------------------
# 데이터베이스 연결 헬퍼
# ------------------------------------------------------------------
def connect_db() -> sqlite3.Connection:
    """
    DB 파일에 연결하고 Connection 객체를 반환함
    """
    return sqlite3.connect(DB_FILE)

# ------------------------------------------------------------------
# 초기화 함수
# ------------------------------------------------------------------
def init_db() -> None:
    """
    매 실행 시 resources 테이블을 삭제 후 재생성하고
    전역 initial_data 목록을 DB에 삽입함
    """
    conn = connect_db()
    cursor = conn.cursor()

    # 기존 테이블 삭제
    cursor.execute('DROP TABLE IF EXISTS resources')

    # 테이블 생성
    cursor.execute('''
        CREATE TABLE resources (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword  TEXT UNIQUE NOT NULL,
            url      TEXT NOT NULL,
            count    INTEGER DEFAULT 0,
            tag      TEXT DEFAULT ''
        )
    ''')

    conn.commit()

    # 전역 initial_data를 DB에 한꺼번에 삽입
    cursor.executemany(
        'INSERT OR IGNORE INTO resources(keyword, url) VALUES (?, ?)',
        initial_data
    )
    conn.commit()

    cursor.close()
    conn.close()

# ------------------------------------------------------------------
# 검색 기능 및 카운트 업데이트
# ------------------------------------------------------------------
def search_resources(query: str) -> List[Tuple[str, str]]:
    """
    SQL WHERE 절로 바로 검색된 결과 반환
    return: [(keyword, url), ...]
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT keyword, url FROM resources WHERE keyword LIKE ?",
            (f"%{query}%",)
        )
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❗ 검색 조회 오류: {e}")
        rows = []
    finally:
        cursor.close()
        conn.close()
    return rows

def update_count(keyword: str) -> None:
    """
    검색된 keyword에 대해 count를 1 증가시킴
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE resources SET count = count + 1 WHERE keyword = ?',
            (keyword,)
        )
        conn.commit()
    except Exception as e:
        print(f"❗ 조회수 업데이트 오류: {e}")
    finally:
        cursor.close()
        conn.close()

# ------------------------------------------------------------------
# 검색 기록 및 히스토리 출력
# ------------------------------------------------------------------
def log_search(query: str) -> None:
    """
    사용자가 입력한 검색어를 HISTORY_FILE에 기록함
    """
    try:
        with open(HISTORY_FILE, 'a', encoding='utf-8') as f:
            f.write(query + '\n')
    except Exception as e:
        print(f"❗ 검색 기록 파일 쓰기 오류: {e}")

def show_history() -> None:
    """
    최근 10개의 검색어를 출력함
    """
    if not os.path.exists(HISTORY_FILE):
        print("검색 기록이 없습니다.")
        return

    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print("⏱️ 최근 검색어:")
        for line in lines[-10:]:
            print(f"- {line.strip()}")
    except Exception as e:
        print(f"❗ 검색 기록 파일 읽기 오류: {e}")

# ------------------------------------------------------------------
# 인기 키워드 Top 5 출력
# ------------------------------------------------------------------
def top_keywords() -> None:
    """
    DB에서 count 순으로 상위 5개 키워드를 출력함
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT keyword, count FROM resources ORDER BY count DESC LIMIT 5')
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❗ 인기 키워드 조회 오류: {e}")
        rows = []
    finally:
        cursor.close()
        conn.close()

    if not rows:
        print("인기 키워드가 없습니다.")
    else:
        print("🔥 인기 키워드 Top 5:")
        for idx, (kw, cnt) in enumerate(rows, start=1):
            print(f"{idx}. {kw} ({cnt}회)")

# ------------------------------------------------------------------
# 유사 키워드 추천
# ------------------------------------------------------------------
def suggest_keywords(query: str) -> List[str]:
    """
    저장된 키워드를 대상으로 difflib로 유사 키워드 추천 (cutoff=0.6)
    return: 추천 키워드 리스트
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT keyword FROM resources')
        all_keys = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print(f"❗ 키워드 목록 조회 오류: {e}")
        all_keys = []
    finally:
        cursor.close()
        conn.close()
    return difflib.get_close_matches(query, all_keys, n=3, cutoff=0.6)

# ------------------------------------------------------------------
# 키워드 추가/삭제/조회/태그 기능
# ------------------------------------------------------------------
def add_resource() -> None:
    """
    새로운 키워드/URL을 DB에 추가
    """
    label = get_msg('search_label')
    kw = input(f"{label} ").strip()
    url = input("URL: ").strip()

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO resources(keyword, url) VALUES(?, ?)', (kw, url))
        conn.commit()
        print(f"✅ '{kw}' 키워드를 성공적으로 추가했습니다.")
    except sqlite3.IntegrityError:
        print(f"❗ 오류: '{kw}' 키워드가 이미 존재합니다.")
    except Exception as e:
        print(f"❗ DB 오류 발생: {e}")
    finally:
        cursor.close()
        conn.close()

def delete_resource() -> None:
    """
    키워드를 DB에서 삭제
    """
    kw = input("삭제할 키워드: ").strip()
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM resources WHERE keyword = ?', (kw,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✅ '{kw}' 키워드를 삭제했습니다.")
        else:
            print(f"❗ '{kw}' 키워드를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❗ DB 삭제 오류: {e}")
    finally:
        cursor.close()
        conn.close()

def list_resources() -> None:
    """
    DB에 등록된 키워드, URL, 검색횟수, 태그 출력
    """
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT keyword, url, count, tag FROM resources')
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❗ 데이터 조회 오류: {e}")
        rows = []
    finally:
        cursor.close()
        conn.close()

    if not rows:
        print("📜 등록된 키워드가 없습니다.")
    else:
        print("📜 등록된 키워드 목록:")
        for kw, url, cnt, tag in rows:
            tag_info = f" [태그: {tag}]" if tag else ""
            print(f"- {kw}: {url} (검색 {cnt}회){tag_info}")

def tag_resource() -> None:
    """
    특정 키워드에 태그 지정
    """
    kw = input("태그를 달 키워드: ").strip()
    tag = input("지정할 태그: ").strip()
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE resources SET tag = ? WHERE keyword = ?', (tag, kw))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"✅ '{kw}'에 태그 '{tag}'를 지정했습니다.")
        else:
            print(f"❗ '{kw}' 키워드를 찾을 수 없습니다.")
    except Exception as e:
        print(f"❗ DB 태그 지정 오류: {e}")
    finally:
        cursor.close()
        conn.close()

def show_by_tag() -> None:
    """
    지정된 태그와 연결된 키워드 목록 출력
    """
    tag = input("검색할 태그: ").strip()
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT keyword, url FROM resources WHERE tag = ?', (tag,))
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❗ DB 태그 조회 오류: {e}")
        rows = []
    finally:
        cursor.close()
        conn.close()

    if not rows:
        print(f"❗ 태그 '{tag}'에 해당하는 키워드가 없습니다.")
    else:
        print(f"🏷️ '{tag}' 태그 키워드:")
        for kw, url in rows:
            print(f"- {kw}: {url}")

# ------------------------------------------------------------------
# 간소화된 도움말 출력
# ------------------------------------------------------------------
def print_help() -> None:
    """
    현재 DB에 등록된 '검색 가능한 키워드' 목록만 출력
    """
    print("검색창에 입력할 수 있는 키워드 목록:")
    for kw, _url in initial_data:
        print(f"  - {kw}")
    print()

# ------------------------------------------------------------------
# 전화번호 검색 기능
# ------------------------------------------------------------------
phonebook = {
    '정보통신공학부': '043-261-2101',
    '학생지원팀'  : '043-261-2114',
    '도서관'      : '043-261-2154',
    '교환학생센터': '043-261-3624',
    '교무팀'      : '043-261-2110',
    '입학처'      : '043-261-2105',
    '학사지원팀'  : '043-261-2130',
    '국제교류본부': '043-261-3299',
    '취업지원센터': '043-261-3661',
    '학생생활관'  : '043-261-2005'
}

def search_phone() -> None:
    """
    부서명을 입력받아 전화번호부에서 조회 후 출력
    """
    dept = input("부서명 입력: ").strip()
    num = phonebook.get(dept)
    if num:
        print(f"{dept} 전화번호: {num}")
    else:
        print("❗ 해당 부서 전화번호가 없습니다.")

# ------------------------------------------------------------------
# 다국어 토글 기능
# ------------------------------------------------------------------
def toggle_language() -> None:
    """
    LANG 변수를 토글하여 다국어 지원 전환
    """
    global LANG
    LANG = 'en' if LANG == 'ko' else 'ko'
    print(get_msg('welcome') if LANG == 'en' else get_msg('exit_msg'))

# ------------------------------------------------------------------
# 단과대학/대학원/연구기관/입학안내/캠퍼스맵 바로가기
# ------------------------------------------------------------------
def open_colleges() -> None:
    """
    단과대학(대학/대학원) 안내 페이지를 브라우저로 엶
    """
    # 충북대학교 메인 페이지(메뉴에서 '대학/대학원 > 단과대학' 클릭 가능)
    url = 'https://www.cbnu.ac.kr/www/index.do'
    try:
        webbrowser.open(url)
        print("📚 단과대학(대학/대학원) 페이지를 열었습니다.")
    except Exception as e:
        print(f"❗ 단과대학 페이지 열기 오류: {e}")

def open_graduate() -> None:
    """
    대학원 안내 페이지를 브라우저로 엶
    """
    url = 'https://graduate.chungbuk.ac.kr/'
    try:
        webbrowser.open(url)
        print("🎓 대학원 페이지를 열었습니다.")
    except Exception as e:
        print(f"❗ 대학원 페이지 열기 오류: {e}")

def open_research() -> None:
    """
    연구/산학 페이지를 브라우저로 엶
    """
    url = 'https://www.cbnu.ac.kr/www/contents.do?key=438'
    try:
        webbrowser.open(url)
        print("🔬 연구/산학 페이지를 열었습니다.")
    except Exception as e:
        print(f"❗ 연구/산학 페이지 열기 오류: {e}")

def open_admission() -> None:
    """
    입학 안내 페이지를 브라우저로 엶
    """
    url = 'https://www.cbnu.ac.kr/www/contents.do?key=395'
    try:
        webbrowser.open(url)
        print("📝 입학 안내 페이지를 열었습니다.")
    except Exception as e:
        print(f"❗ 입학 안내 페이지 열기 오류: {e}")

def open_campusmap() -> None:
    """
    캠퍼스맵 페이지를 브라우저로 엶
    """
    url = 'https://www.cbnu.ac.kr/www/contents.do?key=4'
    try:
        webbrowser.open(url)
        print("🗺️ 캠퍼스맵 페이지를 열었습니다.")
    except Exception as e:
        print(f"❗ 캠퍼스맵 페이지 열기 오류: {e}")

# ------------------------------------------------------------------
# GUI 모드 구현
# ------------------------------------------------------------------
def run_gui() -> None:
    """
    tkinter 기반 GUI 인터페이스 실행
    """
    init_db()   # 실행 시마다 DB 초기화

    root = tk.Tk()
    root.title('CBNU Bot')

    # 언어 전환 버튼
    lang_btn = tk.Button(
        root,
        text=get_msg('lang_button'),
        command=lambda: [
            toggle_language(),
            lang_btn.config(text=get_msg('lang_button')),
            lbl.config(text=get_msg('search_label')),
            search_btn.config(text=get_msg('search_button'))
        ]
    )
    lang_btn.pack(padx=5, pady=5)

    # 검색 라벨
    lbl = tk.Label(root, text=get_msg('search_label'))
    lbl.pack(pady=2)

    # 검색 입력 창
    entry = tk.Entry(root, width=40)
    entry.pack(pady=2)

    # 검색 결과 리스트박스
    lst = tk.Listbox(root, width=60, height=10)
    lst.pack(pady=5)

    # GUI 검색 함수 (브라우저 자동 열기 포함)
    def gui_search() -> None:
        q = entry.get().strip()
        lst.delete(0, tk.END)
        if not q:
            return

        matches = search_resources(q)
        if matches:
            for kw, url in matches:
                lst.insert(tk.END, f"{kw}: {url}")
                update_count(kw)
                webbrowser.open(url)
        else:
            lst.insert(tk.END, get_msg('suggest'))
            for suggestion in suggest_keywords(q):
                lst.insert(tk.END, suggestion)

    # 검색 버튼
    search_btn = tk.Button(
        root,
        text=get_msg('search_button'),
        command=gui_search
    )
    search_btn.pack(pady=5)

    root.mainloop()

# ------------------------------------------------------------------
# 메인 함수 (CLI 모드)
# ------------------------------------------------------------------
def main() -> None:
    """
    프로그램 진입점: CLI 또는 GUI 모드로 분기 처리
    """
    init_db()
    print(get_msg('welcome'))
    print(get_msg('help'))

    while True:
        cmd = input('> ').strip().lower()

        if cmd in ('exit', 'quit'):
            print(get_msg('exit_msg'))
            break

        elif cmd == 'help':
            print_help()

        elif cmd == 'add':
            add_resource()

        elif cmd == 'delete':
            delete_resource()

        elif cmd == 'list':
            list_resources()

        elif cmd == 'history':
            show_history()

        elif cmd == 'top':
            top_keywords()

        elif cmd == 'tag':
            tag_resource()

        elif cmd == 'cat':
            show_by_tag()

        elif cmd == 'colleges':
            open_colleges()

        elif cmd == 'graduate':
            open_graduate()

        elif cmd == 'research':
            open_research()

        elif cmd == 'admission':
            open_admission()

        elif cmd == 'map':
            open_campusmap()

        elif cmd == 'phone':
            search_phone()

        elif cmd == 'lang':
            toggle_language()

        elif cmd == 'gui':
            run_gui()
            break

        else:
            # 일반 검색: 키워드가 DB에 있으면 즉시 브라우저 열기
            log_search(cmd)
            matches = search_resources(cmd)
            if matches:
                for kw, url in matches:
                    print(f"[{kw}] {url}")
                    update_count(kw)
                    webbrowser.open(url)
            else:
                suggestions = suggest_keywords(cmd)
                if suggestions:
                    print(get_msg('suggest'), ', '.join(suggestions))

# ------------------------------------------------------------------
# 엔트리 포인트
# ------------------------------------------------------------------
if __name__ == '__main__':
    # 기본적으로 GUI 모드 실행
    run_gui()
    # CLI 모드로 바로 실행하려면 위 라인을 `main()`으로 바꾸세요.