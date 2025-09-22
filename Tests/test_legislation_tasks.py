from legislation.tasks import fetch_and_process_bills_task
import pytest


def test_fetch_and_process_bills_task():
    assert fetch_and_process_bills_task() is not None, "Task should return a non-None value"