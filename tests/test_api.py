import pytest
from types import SimpleNamespace
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routers.articles import ArticleCreate, ArticleUpdate
from src.models import get_db, TaskHistory


client = TestClient(app)


class TestArticlesAPI:
    def test_get_articles(self):
        response = client.get("/api/articles")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_article_not_found(self):
        response = client.get("/api/articles/999999")
        assert response.status_code == 404
    
    def test_search_articles(self):
        response = client.get("/api/articles/search?q=test")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_category_stats(self):
        response = client.get("/api/articles/stats/categories")
        assert response.status_code == 200
        assert 'categories' in response.json()
    
    def test_daily_stats(self):
        response = client.get("/api/articles/stats/daily?days=7")
        assert response.status_code == 200
        assert 'daily_stats' in response.json()

    def test_article_models_normalize_blank_url(self):
        create_payload = ArticleCreate(title="t", content="c", url="   ")
        assert create_payload.url is None

        update_payload = ArticleUpdate(url="\n")
        dumped = update_payload.model_dump(exclude_unset=True)
        assert dumped.get('url') is None


class TestTasksAPI:
    def test_create_crawl_task(self):
        response = client.post(
            "/api/tasks/crawl",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
        assert 'status' in data
        assert 'message' in data
    
    def test_create_batch_crawl_task(self):
        response = client.post(
            "/api/tasks/crawl/batch",
            json={
                "urls": [
                    "https://example1.com",
                    "https://example2.com"
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert 'task_id' in data
    
    def test_get_active_tasks(self):
        response = client.get("/api/tasks/active")
        assert response.status_code == 200
        assert 'active_tasks' in response.json()
    
    def test_get_scheduled_tasks(self):
        response = client.get("/api/tasks/scheduled")
        assert response.status_code == 200
        assert 'scheduled_tasks' in response.json()

    def test_delete_batch_history_deletes_existing_ids(self):
        deleted_payload = {"task_ids": ["existing-task"]}

        class DummySession:
            def __init__(self):
                self.deleted_task_ids = []
                self.committed = False
                self.rolled_back = False

            def query(self, model):
                assert model is TaskHistory
                return DummyQuery(self)

            def commit(self):
                self.committed = True

            def rollback(self):
                self.rolled_back = True

            def close(self):
                pass

        class DummyQuery:
            def __init__(self, session):
                self.session = session
                self.stage = getattr(session, 'stage', 0)

            def filter(self, *_args, **_kwargs):
                return self

            def all(self):
                self.session.stage = 1
                return [SimpleNamespace(task_id="existing-task")]

            def delete(self, synchronize_session=False):
                assert synchronize_session is False
                self.session.deleted_task_ids = ["existing-task"]
                return len(self.session.deleted_task_ids)

        def override_get_db():
            session = DummySession()
            try:
                yield session
            finally:
                pass

        app.dependency_overrides[get_db] = override_get_db

        try:
            response = client.delete(
                "/api/tasks/history/batch",
                json=deleted_payload
            )
        finally:
            app.dependency_overrides.pop(get_db, None)

        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 1
        assert data["deleted_task_ids"] == ["existing-task"]


class TestAdminAPI:
    def test_get_system_info(self):
        response = client.get("/api/admin/system/info")
        assert response.status_code == 200
        data = response.json()
        assert 'database_status' in data
        assert 'celery_status' in data
        assert 'total_articles' in data
    
    def test_get_workers_status(self):
        response = client.get("/api/admin/workers/status")
        assert response.status_code == 200
        assert 'workers' in response.json()
    
    def test_get_config(self):
        response = client.get("/api/admin/config")
        assert response.status_code == 200
        data = response.json()
        assert 'database' in data
        assert 'redis' in data
        assert 'crawler' in data


class TestHealthCheck:
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert 'version' in data
        assert 'status' in data
    
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
