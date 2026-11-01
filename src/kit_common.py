"""State is separate from the distributable kit and contains private device IDs."""
import json
import os
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('IPHONE_BRIDGE_STATE', str(Path(os.environ['LOCALAPPDATA']) / 'iPhoneWindowsBridge'))).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = ROOT / 'config.json'
CONFIG = json.loads(CONFIG_PATH.read_text(encoding='utf-8-sig')) if CONFIG_PATH.exists() else {}
CONFIG['python'] = str(KIT / 'runtime/python/python.exe')
CONFIG['ios'] = str(KIT / 'runtime/go-ios/ios.exe')
