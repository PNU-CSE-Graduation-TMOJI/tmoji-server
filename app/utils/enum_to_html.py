import inspect
from enum import Enum
from typing import Type

def enum_to_html(enum_cls: Type[Enum]) -> str:
    """
    Enum 클래스를 HTML <ul> 목록 형태로 변환합니다.
    항목의 이름과 docstring을 추출해 아래와 같은 HTML을 생성합니다.

    <h3>EnumClassName</h3>
    <ul>
      <li><strong>VALUE</strong>: 설명</li>
    </ul>
    """
    html = [f"<h3>{enum_cls.__name__}</h3>", "<ul>"]

    for member in enum_cls:
        # 소스 코드에서 주석을 파싱해 docstring 추출
        doc = _get_enum_member_doc(enum_cls, member.name)
        html.append(f"<li><strong>{member.name}</strong>: {doc}</li>")

    html.append("</ul>")
    return "\n".join(html)

def _get_enum_member_doc(enum_cls: Type[Enum], member_name: str) -> str:
    """enum 멤버의 docstring을 소스 코드에서 추출"""
    try:
        source_lines = inspect.getsourcelines(enum_cls)[0]
    except OSError:
        return ""

    for i, line in enumerate(source_lines):
        if line.strip().startswith(f"{member_name} ="):
            # 다음 줄에서 docstring 추출
            if i + 1 < len(source_lines):
                next_line = source_lines[i + 1].strip()
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    return next_line.strip("\"'").strip()
            break
    return ""