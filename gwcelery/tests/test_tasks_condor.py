import subprocess

import pytest

from ..tasks import condor


def get_submit_kwargs(args):
    return {k: v for k, _, v in (a.partition('=') for a in args)}


@pytest.fixture
def mock_condor_submit_aborted(monkeypatch):
    """Simulate submitting a condor job: don't actually do anything, just
    write a log message as if the job was aborted."""

    def mock_check_call(args):
        assert args[0] == 'condor_submit'
        submit_kwargs = get_submit_kwargs(args)

        # Write dummy log message
        with open(submit_kwargs['log'], 'w') as f:
            print('''<c>
                     <a n="MyType"><s>JobAbortedEvent</s></a>
                     <a n="EventTypeNumber"><i>9</i></a>
                     </c>''', file=f)

    monkeypatch.setattr('subprocess.check_call', mock_check_call)


@pytest.fixture
def mock_condor_submit_running(monkeypatch):
    """Simulate submitting a condor job: don't actually do anything, just
    write a log message as if the job was submitted."""

    files_to_remove = []

    def mock_check_call(args):
        assert args[0] == 'condor_submit'
        submit_kwargs = get_submit_kwargs(args)
        files_to_remove.extend(
            submit_kwargs[key] for key in ['log', 'error', 'output'])

        # Write dummy log message
        with open(submit_kwargs['log'], 'w') as f:
            print('''<c>
                     <a n="MyType"><s>JobImageSizeEvent</s></a>
                     <a n="Subproc"><i>0</i></a>
                     <a n="EventTypeNumber"><i>6</i></a>
                     </c>''', file=f)

    monkeypatch.setattr('subprocess.check_call', mock_check_call)
    yield
    # Clean up log files
    condor._rm_f(*files_to_remove)


@pytest.fixture
def mock_condor_submit(monkeypatch):
    """Simulate submitting a condor job by running the underlying executable
    right away and writing the status of the executable to the log file."""

    def mock_check_call(args):
        assert args[0] == 'condor_submit'
        submit_kwargs = get_submit_kwargs(args)

        with open(submit_kwargs['error'], 'w') as stderr, \
                open(submit_kwargs['output'], 'w') as stdout:
            returncode = subprocess.call(
                submit_kwargs['arguments'][1:-1].split(),
                stderr=stderr, stdout=stdout)

        with open(submit_kwargs['log'], 'w') as f:
            print('''<c>
                     <a n="SentBytes"><r>0.0</r></a>
                     <a n="ReturnValue"><i>{}</i></a>
                     <a n="TerminatedNormally"><b v="t"/></a>
                     <a n="MyType"><s>JobTerminatedEvent</s></a>
                     <a n="EventTypeNumber"><i>5</i></a>
                     </c>'''.format(returncode), file=f)

    monkeypatch.setattr('subprocess.check_call', mock_check_call)


def test_check_output_error_on_submit(monkeypatch):
    """Test capturing an error from condor_submit."""

    accounting_group = 'foo.bar'
    cmd = ('sleep', '1')
    msg = 'no such accounting group'  # fake accounting group error

    def mock_check_call(args):
        raise subprocess.CalledProcessError(1, args, msg)

    monkeypatch.setattr('subprocess.check_call', mock_check_call)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        condor.check_output.delay(cmd, accounting_group=accounting_group)
    assert 'accounting_group=' + accounting_group in exc_info.value.cmd
    assert exc_info.value.output == msg


def test_check_output_aborted(mock_condor_submit_aborted):
    """Test a job that is aborted."""

    with pytest.raises(condor.JobAborted):
        condor.check_output.delay(['sleep', '1'])


def test_check_output_fails(mock_condor_submit):
    """Test a job that immediately fails."""

    with pytest.raises(condor.JobFailed) as exc_info:
        condor.check_output.delay(['sleep', '--foo="bar bat"', '1'])
    assert exc_info.value.returncode == 1


# FIXME: this test doesn't work in eager mode.
# def test_check_output_running(mock_condor_submit_running):
#
#     with pytest.raises(condor.JobRunning):
#         condor.check_output.delay(['sleep', '1'])


# FIXME: this test doesn't work in eager mode.
# See https://github.com/celery/celery/issues/4661.
# def test_check_output_succeeds(mock_condor_submit):
#     """Test a job that immediately succeeds."""
#
#     condor.check_output.delay(['sleep', '1'])
