from pydantic import BaseModel, ConfigDict

class CommonModel(BaseModel):
  model_config = ConfigDict(
    alias_generator=lambda s: ''.join(
      [s.split('_')[0]] + [w.capitalize() for w in s.split('_')[1:]]
    ),
    populate_by_name=True
  )