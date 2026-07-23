import pytest


@pytest.fixture()
def data_root(tmp_path):
    root = str(tmp_path).replace("\\", "/") + "/"
    return root


@pytest.fixture()
def wifi():
    from lib.networking import WirelessNetwork
    return WirelessNetwork()


@pytest.fixture()
def relay_history(data_root, wifi):
    import config
    config.RELAY_HISTORY_ENABLED = True
    from lib.relay_history import RelayHistory
    return RelayHistory(wifi, data_root)


def test_init_creates_state_file_structure(data_root, relay_history):
    """
    Test that the data/relay folder structure is created under the given root.
    """
    from os import path
    assert path.isdir(data_root + "data")
    assert path.isdir(data_root + "data/relay")


def test_disabled_history_is_a_no_op(data_root, wifi):
    """
    Test that a disabled RelayHistory does not create files or track state.
    """
    import config
    config.RELAY_HISTORY_ENABLED = False
    from lib.relay_history import RelayHistory
    history = RelayHistory(wifi, data_root)

    from os import path
    assert not path.isdir(data_root + "data")

    history.record_transition(True)
    assert history.get_total_active_seconds() is None
    assert history.reset() is None


def test_get_total_active_seconds_with_no_state_file_is_zero(relay_history):
    """
    Test that a freshly initialised history with no transitions returns zero on time.
    """
    assert relay_history.get_total_active_seconds() == 0


def test_record_transition_persists_state(relay_history):
    """
    Test that recording a transition persists the active flag to the state file.
    Note: with no asyncio event loop running (as in this synchronous test), the
    SMIB push inside record_transition fails to schedule and is caught, which
    is exercised separately in test_record_transition_enables_push_error_without_event_loop.
    """
    relay_history.record_transition(True)
    state = relay_history.get_current_state()
    assert state is not None
    assert state["active"] is True


def test_record_transition_enables_push_error_without_event_loop(relay_history):
    """
    Test that attempting to push to SMIB with no running asyncio event loop
    (as is the case outside of the device's real async runtime) is caught and
    surfaces as an enabled PUSH error via the module's error handler, rather
    than raising out of record_transition.
    """
    relay_history.record_transition(True)
    assert relay_history.error_handler.is_error_enabled("PUSH")


def test_total_active_seconds_accumulates_across_on_off_cycle(relay_history, monkeypatch):
    """
    Test that going active then inactive accumulates the elapsed active duration
    into total_active_seconds.
    """
    import lib.relay_history as relay_history_module

    fake_time = [1000.0]
    monkeypatch.setattr(relay_history_module, "time", lambda: fake_time[0])

    relay_history.record_transition(True)
    fake_time[0] += 60
    relay_history.record_transition(False)

    assert relay_history.get_total_active_seconds() == 60


def test_get_total_active_seconds_counts_in_progress_active_time(relay_history, monkeypatch):
    """
    Test that on time is live-calculated while the relay is currently active,
    without requiring another transition first.
    """
    import lib.relay_history as relay_history_module

    fake_time = [1000.0]
    monkeypatch.setattr(relay_history_module, "time", lambda: fake_time[0])

    relay_history.record_transition(True)
    fake_time[0] += 30

    assert relay_history.get_total_active_seconds() == 30


def test_reset_zeroes_total_and_returns_previous_value(relay_history, monkeypatch):
    """
    Test that reset returns the total that was reset and zeroes the running total,
    while preserving the current active state.
    """
    import lib.relay_history as relay_history_module

    fake_time = [1000.0]
    monkeypatch.setattr(relay_history_module, "time", lambda: fake_time[0])

    relay_history.record_transition(True)
    fake_time[0] += 45

    previous_total = relay_history.reset()

    assert previous_total == 45
    assert relay_history.get_total_active_seconds() == 0
    state = relay_history.get_current_state()
    assert state["active"] is True


def test_heartbeat_refreshes_timestamp_without_losing_accumulated_total(relay_history, monkeypatch):
    """
    Test that a heartbeat while active folds elapsed time into the total and
    refreshes the recorded timestamp, without changing the active state.
    """
    import lib.relay_history as relay_history_module

    fake_time = [1000.0]
    monkeypatch.setattr(relay_history_module, "time", lambda: fake_time[0])

    relay_history.record_transition(True)
    fake_time[0] += 3600
    relay_history.heartbeat()

    state = relay_history.get_current_state()
    assert state["active"] is True
    assert state["timestamp"] == 4600.0
    assert relay_history.get_total_active_seconds() == 3600


def test_heartbeat_clears_heartbeat_error_on_success(relay_history):
    """
    Test that a successful heartbeat disables the HEARTBEAT error if it was enabled.
    """
    relay_history.error_handler.enable_error("HEARTBEAT")
    relay_history.heartbeat()
    assert not relay_history.error_handler.is_error_enabled("HEARTBEAT")


def test_check_and_recover_on_boot_credits_only_up_to_last_timestamp(relay_history, monkeypatch):
    """
    Test that on boot, if the relay was left active, on time is only credited
    up to the last recorded timestamp - not through to the current boot time -
    and the relay is marked inactive afterwards.
    """
    import lib.relay_history as relay_history_module

    fake_time = [1000.0]
    monkeypatch.setattr(relay_history_module, "time", lambda: fake_time[0])

    relay_history.record_transition(True)
    fake_time[0] += 20
    relay_history.heartbeat()

    # Simulate an unplug: a large gap passes with no further writes before reboot
    fake_time[0] += 999999

    relay_history.check_and_recover_on_boot()

    state = relay_history.get_current_state()
    assert state["active"] is False
    # Only the 20 seconds between the transition and the heartbeat should be credited,
    # not the 999999 second gap while presumed unplugged.
    assert relay_history.get_total_active_seconds() == 20


def test_check_and_recover_on_boot_with_no_existing_state_file(data_root, wifi):
    """
    Test that boot recovery on a brand new device (no prior state file) initialises
    a zeroed, inactive state without error.
    """
    import config
    config.RELAY_HISTORY_ENABLED = True
    from lib.relay_history import RelayHistory
    history = RelayHistory(wifi, data_root)

    history.check_and_recover_on_boot()

    state = history.get_current_state()
    assert state["active"] is False
    assert state["total_active_seconds"] == 0
