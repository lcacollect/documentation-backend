import pytest


@pytest.mark.asyncio
async def test_gzip_middleware_is_active(app):
    assert app.user_middleware[1].cls.__name__ == "GZipMiddleware"
    assert app.user_middleware[1].options == {"minimum_size": 1024}
