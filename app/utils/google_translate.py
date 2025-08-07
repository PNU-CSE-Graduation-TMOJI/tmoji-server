from typing import cast
from google.cloud import translate_v2 # pyright: ignore[reportMissingTypeStubs]

from app.models.enums.service import Language 

language_converter: dict[Language, str] = {
  Language.EN: 'en',
  Language.JP: 'ja',
  Language.KO: 'ko',
}

def translate_text(target: Language, source: Language, text: str) -> str:
    """Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    translate_client = translate_v2.Client()

    if isinstance(text, bytes):
      text = text.decode("utf-8")

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = cast(
      dict[str, str], 
      translate_client.translate(  # pyright: ignore[reportUnknownMemberType]
        text, 
        target_language=language_converter[target],
        source_language=language_converter[source],
      )
    )

    print("Text: {}".format(result["input"]))
    print("Translation: {}".format(result["translatedText"]))

    return result["translatedText"]