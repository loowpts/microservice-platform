import pytest
from apps.content.models import Channel
from apps.posts.models import Post


@pytest.mark.unit
@pytest.mark.models
class TestChannelModel:
    def test_channel_creation(self, channel):
        assert channel.name == 'Test Channel'
        assert channel.slug == 'test-channel'
        assert channel.owner_id == 1
        assert channel.description == 'Test channel description'

    