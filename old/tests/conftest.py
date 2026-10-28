import os
import tempfile
os.environ["CHEMELLM_DATA_DIR"]=tempfile.mkdtemp(prefix="chemellm-tests-")

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, execute, uid, now

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def project_id():
    init_db()
    ident=uid()
    execute("INSERT INTO projects VALUES(?,?,?)",(ident,"测试工程",now()))
    return ident
