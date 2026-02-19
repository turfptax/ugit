"""Tests for config creation, loading, and resolution."""
import ugit


class TestCreateAndLoadConfig:
    """Round-trip tests for create_config() / _load_config()."""

    def test_round_trip_all_fields(self, mock_filesystem):
        ugit.create_config(
            ssid='TestWifi',
            password='TestPass',
            user='testuser',
            repository='testrepo',
            branch='dev',
            token='ghp_test',
            ignore=['/data']
        )
        cfg = ugit._load_config()
        assert cfg['ssid'] == 'TestWifi'
        assert cfg['password'] == 'TestPass'
        assert cfg['user'] == 'testuser'
        assert cfg['repository'] == 'testrepo'
        assert cfg['branch'] == 'dev'
        assert cfg['token'] == 'ghp_test'
        assert cfg['ignore'] == ['/data']

    def test_load_missing_config_returns_empty(self, mock_filesystem):
        cfg = ugit._load_config()
        assert cfg == {}

    def test_default_branch_is_main(self, mock_filesystem):
        ugit.create_config(ssid='x', password='y', user='u', repository='r')
        cfg = ugit._load_config()
        assert cfg['branch'] == 'main'

    def test_default_ignore_is_empty(self, mock_filesystem):
        ugit.create_config(ssid='x', password='y', user='u', repository='r')
        cfg = ugit._load_config()
        assert cfg['ignore'] == []


class TestResolveConfig:
    """Tests for _resolve_config() argument-vs-config priority."""

    def test_args_override_config(self, mock_filesystem):
        ugit.create_config(ssid='cfg_wifi', password='cfg_pass',
                           user='cfg_user', repository='cfg_repo')
        result = ugit._resolve_config(user='arg_user')
        assert result['user'] == 'arg_user'
        assert result['ssid'] == 'cfg_wifi'  # from config

    def test_no_config_no_args(self, mock_filesystem):
        result = ugit._resolve_config()
        assert result['user'] == ''
        assert result['branch'] == 'main'

    def test_token_none_reads_config(self, mock_filesystem):
        ugit.create_config(ssid='x', password='y', user='u',
                           repository='r', token='ghp_from_config')
        result = ugit._resolve_config(token=None)
        assert result['token'] == 'ghp_from_config'

    def test_token_empty_string_overrides_config(self, mock_filesystem):
        ugit.create_config(ssid='x', password='y', user='u',
                           repository='r', token='ghp_from_config')
        # token='' is not None, so it overrides
        result = ugit._resolve_config(token='')
        assert result['token'] == ''

    def test_ignore_none_reads_config(self, mock_filesystem):
        ugit.create_config(ssid='x', password='y', user='u',
                           repository='r', ignore=['/data'])
        result = ugit._resolve_config(ignore=None)
        assert result['ignore'] == ['/data']

    def test_ignore_explicit_overrides_config(self, mock_filesystem):
        ugit.create_config(ssid='x', password='y', user='u',
                           repository='r', ignore=['/data'])
        result = ugit._resolve_config(ignore=['/other'])
        assert result['ignore'] == ['/other']
