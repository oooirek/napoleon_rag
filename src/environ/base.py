from pathlib import Path

from pydantic_settings import SettingsConfigDict

ENV_FILE = Path(__file__).parent.parent.parent.joinpath(".env")

BASE_MODEL_CONFIG = SettingsConfigDict(
	env_file=ENV_FILE,
	extra="ignore",
	validate_default=True,
	frozen=True,
)
