from enum import Enum

class ServiceMode(str, Enum):
  MACHINE = "MACHINE"
  """기계 번역 모드"""

  AI = "AI"
  """AI 번역 모드"""

class ServiceStep(str, Enum):
  BOUNDING = "BOUNDING"
  """바운딩 박스 (영역) 생성 단계"""

  DETECTING = "DETECTING"
  """바운딩 박스로 OCR 인식 단계"""

  TRANSLATING = "TRANSLATING"
  """인식된 텍스트 번역 단계"""

  COMPOSING = "COMPOSING"
  """TextCtrl 합성 단계"""

class ServiceStatus(str, Enum):
  PENDING = "PENDING"
  """로딩이 끝나고 입력 대기 상태"""

  PROCESSING = "PROCESSING"
  """각 단계 별 AI가 수행 중, (수정 불가 & 삭제 불가, `BOUNDING` 제외)"""

  COMPLETED = "COMPLETED"
  """`COMPOSING` 이 끝나서 완전히 완료된 상태"""

  FAILED = "FAILED"
  """일련의 과정 중 알 수 없는 에러로 진행할 수 없는 상태"""

class Language(str, Enum):
  EN = "EN"
  """ENGLISH, 영어"""

  KO = "KO"
  """KOREAN, 한국어"""

  JP = "JP"
  """JAPANESE, 일본어"""