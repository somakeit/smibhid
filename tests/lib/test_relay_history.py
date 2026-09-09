import pytest


@pytest.fixture()
def data_root(tmp_path):
    root = str(tmp_path).replace("\\", "/") + "/"
    return root


@pytest.fixture()
def slack_api():
    from lib.networking import WirelessNetwork
    from lib.slack_api import Wrapper
    return Wrapper(WirelessNetwork())


@pytest.fixture()
def relay_history(data_root, slack_api):
    import config
    config.SPACE_OPEN_RELAY_HISTORY_ENABLED = True
    from lib.relay_history import RelayHistory
    return RelayHistory(slack_api, data_root)


@pytest.fixture()
def fake_time(monkeypatch):
    """
    Patch time() with a mutable clock seeded well after the RTC sanity
    floor, since accumulation is driven by wall-clock diffs and any
    reading before the floor is treated as unreliable and skipped.
    """
    import lib.relay_history as relay_history_module

    current_time = [relay_history_module.RTC_SANITY_FLOOR_EPOCH_S + 1000]
    monkeypatch.setattr(relay_history_module, "time", lambda: current_time[0])
    return current_time


def test_init_creates_state_file_structure(data_root, relay_history):
    """
    Test that the data/relay folder structure is created under the given root.
    """
    from os import path
    assert path.isdir(data_root + "data")
    assert path.isdir(data_root + "data/relay")


def test_init_disables_history_if_folder_creation_fails(data_root, slack_api, monkeypatch):
    """
    Test that if the state folder can't be created (e.g. full/read-only
    filesystem), RelayHistory disables itself at construction rather than
    leaving enabled True and failing every subsequent write indefinitely.
    """
    import config
    config.SPACE_OPEN_RELAY_HISTORY_ENABLED = True
    import lib.relay_history as relay_history_module
    import lib.utils as utils_module

    def failing_mkdir(*args, **kwargs):
        raise OSError("Read-only filesystem")

    monkeypatch.setattr(utils_module, "mkdir", failing_mkdir)

    history = relay_history_module.RelayHistory(slack_api, data_root)

    assert history.enabled is False
    assert history.error_handler.is_error_enabled("INIT")


def test_disabled_history_is_a_no_op(data_root, slack_api):
    """
    Test that a disabled RelayHistory does not create files or track state.
    """
    import config
    config.SPACE_OPEN_RELAY_HISTORY_ENABLED = False
    from lib.relay_history import RelayHistory
    history = RelayHistory(slack_api, data_root)

    from os import path
    assert not path.isdir(data_root + "data")

    history.record_transition(False, True)
    assert history.get_total_active_seconds(True) is None
    assert history.reset(True) is None


def test_get_total_active_seconds_with_no_prior_state_is_zero(relay_history, fake_time):
    """
    Test that a freshly initialised history with no prior state returns zero on time.
    """
    assert relay_history.get_total_active_seconds(False) == 0


def test_missing_state_file_is_seeded_with_a_zeroed_write(relay_history, fake_time):
    """
    Test that finding no state file to read writes a zeroed one there and
    then, rather than counting in memory until the first transition or
    heartbeat, so the backup file exists and is inspectable from the
    outset.
    """
    from os import path
    assert not path.exists(relay_history.STATE_FILE)

    relay_history.get_total_active_seconds(False)

    from json import loads
    with open(relay_history.STATE_FILE, "r") as f:
        state = loads(f.read())

    assert state["total_active_seconds"] == 0
    assert state["timestamp"] == fake_time[0]
    assert state["human_timestamp"]


def test_get_total_active_seconds_before_rtc_sanity_floor_raises(relay_history, monkeypatch):
    """
    Test that querying on time before the clock has been NTP-corrected
    (reads before the 2024 sanity floor) raises RTCUnreliableError rather
    than returning a meaningless figure, and surfaces the CLOCK error.
    """
    import lib.relay_history as relay_history_module
    monkeypatch.setattr(relay_history_module, "time", lambda: 1000.0)

    with pytest.raises(relay_history_module.RTCUnreliableError):
        relay_history.get_total_active_seconds(False)
    assert relay_history.error_handler.is_error_enabled("CLOCK")


def test_record_transition_persists_state(relay_history, fake_time):
    """
    Test that recording a transition updates the total (here 0, since
    off->on adds no elapsed time) without error.
    Note: with no asyncio event loop running (as in this synchronous test), the
    SMIB push inside record_transition fails to schedule and is caught, which
    is exercised separately in test_record_transition_enables_push_error_without_event_loop.
    """
    relay_history.record_transition(False, True)
    assert relay_history.get_total_active_seconds(True) == 0


def test_record_transition_enables_push_error_without_event_loop(relay_history, fake_time):
    """
    Test that attempting to push to SMIB with no running asyncio event loop
    (as is the case outside of the device's real async runtime) is caught and
    surfaces as an enabled PUSH error via the module's error handler, rather
    than raising out of record_transition.
    """
    relay_history.record_transition(False, True)
    assert relay_history.error_handler.is_error_enabled("PUSH")


def test_on_to_off_transition_credits_elapsed_active_time(relay_history, fake_time):
    """
    Test that going from on to off credits the elapsed time since the
    last checkpoint into the total.
    """
    relay_history.record_transition(False, True)
    fake_time[0] += 60
    relay_history.record_transition(True, False)

    assert relay_history.get_total_active_seconds(False) == 60


def test_off_to_off_heartbeat_does_not_accumulate_time(relay_history, fake_time):
    """
    Test that a heartbeat while off (previous_active == active == False)
    never adds elapsed time, regardless of how long has passed.
    """
    fake_time[0] += 60
    relay_history.heartbeat(False)

    assert relay_history.get_total_active_seconds(False) == 0


def test_heartbeat_returns_true_on_success(relay_history, fake_time):
    """
    Test that heartbeat() reports success when the clock is reliable.
    """
    assert relay_history.heartbeat(False) is True


def test_heartbeat_returns_false_before_rtc_sanity_floor(relay_history, monkeypatch):
    """
    Test that heartbeat() reports failure while the clock is unreliable,
    rather than raising, so a caller retrying on a timer can react without
    needing to catch an exception.
    """
    import lib.relay_history as relay_history_module
    monkeypatch.setattr(relay_history_module, "time", lambda: 1000.0)

    assert relay_history.heartbeat(False) is False


def test_on_to_on_heartbeat_accumulates_elapsed_time_and_advances_checkpoint(relay_history, fake_time):
    """
    Test that a heartbeat while on (previous_active == active == True)
    credits elapsed time since the last checkpoint and advances the
    checkpoint, so a second heartbeat only credits the time since the
    first one, not from the original transition.
    """
    relay_history.record_transition(False, True)
    fake_time[0] += 3600
    relay_history.heartbeat(True)
    fake_time[0] += 3600
    relay_history.heartbeat(True)

    assert relay_history.get_total_active_seconds(True) == 7200


def test_get_total_active_seconds_live_calculates_without_side_effects(relay_history, fake_time):
    """
    Test that get_total_active_seconds returns a live, up-to-date figure
    reflecting time elapsed since the last checkpoint even without a
    heartbeat or transition having happened yet - so a caller like the
    web UI never has to wait up to an hour for a fresh number - and that
    calling it repeatedly does not itself advance the checkpoint or alter
    the persisted total (a pure read).
    """
    relay_history.record_transition(False, True)
    fake_time[0] += 30

    assert relay_history.get_total_active_seconds(True) == 30

    fake_time[0] += 15
    assert relay_history.get_total_active_seconds(True) == 45

    # A transition now should credit the full 45s, proving the reads
    # above didn't advance the checkpoint themselves.
    relay_history.record_transition(True, False)
    assert relay_history.get_total_active_seconds(False) == 45


def test_reset_zeroes_total_and_returns_previous_value(relay_history, fake_time):
    """
    Test that reset returns the live-calculated total that was reset and
    zeroes the running total.
    """
    relay_history.record_transition(False, True)
    fake_time[0] += 45

    previous_total = relay_history.reset(True)

    assert previous_total == 45
    assert relay_history.get_total_active_seconds(True) == 0


def test_reset_while_active_does_not_recredit_time_already_reset(relay_history, fake_time):
    """
    Test that resetting while the relay is active advances the checkpoint,
    so time already folded into the zeroed total isn't re-credited on the
    next read - only time elapsed since the reset itself should count.
    """
    relay_history.record_transition(False, True)
    fake_time[0] += 45

    relay_history.reset(True)

    fake_time[0] += 10
    assert relay_history.get_total_active_seconds(True) == 10


def test_reset_writes_state_exactly_once(relay_history, fake_time):
    """
    Test that reset() persists exactly one write.
    """
    relay_history.record_transition(False, True)
    fake_time[0] += 45

    write_calls = []
    original_write_state = relay_history._write_state

    def counting_write_state(*args, **kwargs):
        write_calls.append(args)
        return original_write_state(*args, **kwargs)

    relay_history._write_state = counting_write_state

    relay_history.reset(True)

    assert len(write_calls) == 1


def test_reset_before_rtc_sanity_floor_raises_and_does_not_write(relay_history, monkeypatch):
    """
    Test that reset() refuses to act while the clock is unreliable,
    rather than zeroing a total calculated from a meaningless diff.
    """
    import lib.relay_history as relay_history_module
    monkeypatch.setattr(relay_history_module, "time", lambda: 1000.0)

    write_calls = []
    original_write_state = relay_history._write_state

    def counting_write_state(*args, **kwargs):
        write_calls.append(args)
        return original_write_state(*args, **kwargs)

    relay_history._write_state = counting_write_state

    with pytest.raises(relay_history_module.RTCUnreliableError):
        relay_history.reset(True)
    assert len(write_calls) == 0


def test_restores_total_from_file_after_reconstruction(data_root, slack_api, fake_time):
    """
    Test that a new RelayHistory instance (simulating a reboot) restores
    the total previously backed up to file.
    """
    import config
    config.SPACE_OPEN_RELAY_HISTORY_ENABLED = True
    from lib.relay_history import RelayHistory

    first = RelayHistory(slack_api, data_root)
    first.record_transition(False, True)
    fake_time[0] += 20
    first.record_transition(True, False)

    second = RelayHistory(slack_api, data_root)
    assert second.get_total_active_seconds(False) == 20


def test_restores_zero_if_state_file_is_corrupt(relay_history, fake_time):
    """
    Test that a corrupted state file (implausible total_active_seconds)
    is not trusted - the total falls back to zero rather than
    propagating a bad value forever.
    """
    with open(relay_history.STATE_FILE, "w") as f:
        f.write('{"total_active_seconds": -5}')

    assert relay_history.get_total_active_seconds(False) == 0


def test_reset_raises_and_skips_smib_push_if_state_write_fails(relay_history, fake_time):
    """
    Test that reset() raises rather than reporting success or notifying SMIB
    if the state file write fails, so a persistence failure can't look like a
    successful reset to callers while smibhid's own total silently reverts.
    """
    relay_history.STATE_FILE = relay_history.STATE_FILE.replace("state.json", "missing_dir/state.json")

    with pytest.raises(RuntimeError):
        relay_history.reset(False)

    assert relay_history.error_handler.is_error_enabled("WRITE")


def test_record_transition_still_pushes_to_smib_if_state_write_fails(relay_history, fake_time):
    """
    Test that record_transition() still attempts to push to SMIB even if the
    local state file write fails. Relay transitions are driven by real-world
    space/light state changes outside smibhid's control, so SMIB must be
    told regardless of whether smibhid persisted it locally - any resulting
    discrepancy is diagnosable as smibhid-side, with SMIB's own total
    remaining the trusted figure. The push itself still fails here because
    there's no running asyncio event loop, which is what enables PUSH.
    """
    relay_history.STATE_FILE = relay_history.STATE_FILE.replace("state.json", "missing_dir/state.json")

    relay_history.record_transition(False, True)

    assert relay_history.error_handler.is_error_enabled("WRITE")
    assert relay_history.error_handler.is_error_enabled("PUSH")
