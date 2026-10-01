import os
import tempfile

# Must be set before the backend is imported.
os.environ["MOCK_LLM"] = "true"
os.environ["KAAVAL_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["OWNER_PASSCODE"] = "test-pass"
