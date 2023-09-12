from plugins import conf

if conf.loadtype == conf.LoadType.STANDALONE_CODE:
    from plugins import api as _api
    import sys
    # remote_api = _api.API()

    remote_api = _api.RemoteAPIModule.api_factory('rixa.remote_api')
    sys.modules['rixa.remote_api'] = remote_api

