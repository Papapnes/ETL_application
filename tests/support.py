from streamlit.testing.v1 import AppTest

from accounts.config import database_path
from accounts.service import Accounts


def signed_in_app(path, default_timeout=30):
    service = Accounts(database_path())
    service.register("Test Client", "client@example.com", "test-password-long-2026")
    token = service.login("client@example.com", "test-password-long-2026")
    app = AppTest.from_file(path, default_timeout=default_timeout)
    app.session_state["auth_token"] = token
    return app
