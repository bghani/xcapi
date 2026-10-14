"""Offline tests: no network access or API key needed.  Run with:  pytest tests/"""
import json
import pytest
from unittest import mock

from xcapi.query import QueryBuilder as Q
from xcapi.client import XenoCantoClient
from xcapi.downloader import Downloader


# ---------- QueryBuilder ---------------------------------------------------

@pytest.mark.parametrize("build, expected", [
    (lambda: Q().year("2015-2020"), 'year:">2014" year:"<2021"'),
    (lambda: Q().year(">2018"), 'year:">2018"'),
    (lambda: Q().month("1-3"), 'month:">0" month:"<4"'),
    (lambda: Q().sample_rate("44100-96000"), 'smp:">44099" smp:"<96001"'),
    (lambda: Q().temperature("20-30"), 'temp:">19" temp:"<31"'),
    (lambda: Q().latitude("40-45"), "box:40,-180,45,180"),
    (lambda: Q().latitude("40-45").longitude("-10-0"), "box:40,-10,45,0"),
    (lambda: Q().latitude(">66.5"), 'lat:">66.5"'),
    (lambda: Q().xc_number("88888-88890"), "nr:88888-88890"),
    (lambda: Q().quality(">C"), 'q:">C"'),
    (lambda: Q().length("10-20"), 'len:10-20'),
])
def test_query_strings(build, expected):
    assert build().build() == expected


@pytest.mark.parametrize("bad", [
    lambda: Q().xc_number("<800000"),
    lambda: Q().xc_number(">1"),
    lambda: Q().year("2020-2015"),
    lambda: Q().bounding_box(1, 2, 3, 4).latitude("1-2").build(),
])
def test_invalid_queries_raise(bad):
    with pytest.raises(ValueError):
        bad()


@pytest.mark.parametrize("name", ["altitude", "uploaded", "time_of_day"])
def test_removed_methods(name):
    assert not hasattr(Q(), name)


# ---------- Client ---------------------------------------------------------

def _response(status, payload):
    r = mock.Mock()
    r.status_code = status
    r.ok = status < 400
    r.json.return_value = payload
    return r


def test_api_error_message_is_surfaced_and_key_hidden():
    c = XenoCantoClient(api_key="SECRETKEY")
    c.session.get = mock.Mock(return_value=_response(
        400, {"error": {"code": "invalid_tag", "message": "Unknown tag alt"}}))
    with pytest.raises(RuntimeError) as e:
        c._fetch_page("alt:100", 1, 50)
    assert "Unknown tag alt" in str(e.value)
    assert "SECRETKEY" not in str(e.value)


def test_zero_results_warns():
    c = XenoCantoClient(api_key="k")
    c.session.get = mock.Mock(return_value=_response(
        200, {"numRecordings": "0", "page": 1, "numPages": 1, "recordings": []}))
    with pytest.warns(UserWarning, match="No recordings matched"):
        assert c.search("nr:1") == []


# ---------- Downloader -----------------------------------------------------

def _recs(n, start=1):
    return [{"id": str(i), "gen": "Gryllus", "sp": "campestris", "file": f"https://x/{i}"}
            for i in range(start, start + n)]


def test_progress_survives_interrupt(tmp_path):
    d = Downloader(output_dir=str(tmp_path))
    d.SAVE_EVERY = 10
    calls = {"n": 0}

    def fake_download(rec, verbose):
        calls["n"] += 1
        if calls["n"] == 23:
            raise KeyboardInterrupt

    with mock.patch.object(d, "_download_recording", side_effect=fake_download):
        with pytest.raises(KeyboardInterrupt):
            d.download_recordings(_recs(50))

    runs = json.loads((tmp_path / "xcapi_runs.json").read_text())
    saved = [i for ids in runs.values() for i in ids]
    assert saved == [str(i) for i in range(1, 23)]          # all 22 completed downloads kept
    assert len((tmp_path / "metadata.csv").read_text().splitlines()) == 23  # header + 22


def test_rerun_skips_saved_and_restricted(tmp_path):
    d = Downloader(output_dir=str(tmp_path))
    with mock.patch.object(d, "_download_recording"):
        d.download_recordings(_recs(5))
        recs = _recs(7) + [{"id": "99", "gen": "A", "sp": "b", "file": "restricted_species",
                            "_meta": {"redacted_fields": {"file": "restricted_species"}}}]
        stats = d.download_recordings(recs)
    assert stats == {"downloaded": 2, "skipped": 5, "restricted": 1, "failed": 0}


def test_redownload_overwrites_only_once(tmp_path):
    d = Downloader(output_dir=str(tmp_path))
    d.SAVE_EVERY = 3
    with mock.patch.object(d, "_download_recording"):
        d.download_recordings(_recs(4))
        d.download_recordings(_recs(10, start=100), redownload=True)
    lines = (tmp_path / "metadata.csv").read_text().splitlines()
    assert len(lines) == 11          # header + the 10 redownloaded, none lost between flushes
    runs = json.loads((tmp_path / "xcapi_runs.json").read_text())
    assert len(runs) == 1 and len(next(iter(runs.values()))) == 10

def test_api_error_real_format():
    c = XenoCantoClient(api_key="SECRETKEY")
    c.session.get = mock.Mock(return_value=_response(
        400, {"error": "client_error",
              "message": "Xeno-canto API v3 only accepts queries using tags."}))
    with pytest.raises(RuntimeError) as e:
        c._fetch_page("grp:birds alt:100", 1, 50)
    assert "only accepts queries using tags" in str(e.value)
    assert "SECRETKEY" not in str(e.value)