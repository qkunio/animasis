from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from animasis.cli import main
from animasis.publishing import _SAU_ROOT


def test_publish_command_forwards_to_sau():
    argv = ["douyin", "check", "--account", "creator"]
    with patch("animasis.publishing.main", return_value=0) as publish:
        assert main(["publish", *argv]) == 0
    publish.assert_called_once_with(argv)


def test_douyin_upload_bypasses_csp():
    source = (_SAU_ROOT / "uploader" / "douyin_uploader" / "main.py").read_text(encoding="utf-8")
    video_upload = source.split("async def upload(self, playwright: Playwright) -> None:", 1)[1]
    assert "bypass_csp=True" in video_upload.split("context = await set_init_script(context)", 1)[0]


def test_sau_state_dir_honors_env(tmp_path: Path):
    state_dir = tmp_path / "state"
    env = os.environ.copy()
    env["ANIMASIS_SAU_HOME"] = str(state_dir)
    code = (
        "from animasis.publishing import _activate_sau; "
        "_activate_sau(); import conf; print(conf.BASE_DIR)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert Path(completed.stdout.strip()) == state_dir
