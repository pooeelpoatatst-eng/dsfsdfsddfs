from app.services.public_audio import public_searches


def test_public_audio_uses_an_alternate_public_source_before_youtube() -> None:
    searches = public_searches("Artist — Track")
    assert searches[0] == "scsearch1:Artist — Track"
    assert searches[1] == "ytsearch1:Artist — Track"
