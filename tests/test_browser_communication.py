import asyncio
import json
import pytest
from unittest.mock import MagicMock
from blastai.scheduler import Scheduler
from blastai.resource_manager import ResourceManager
from blastai.config import Constraints, Settings
from blastai.tools import Tools

@pytest.mark.asyncio
async def test_inter_browser_communication():
    # Setup mocks
    constraints = Constraints(max_concurrent_browsers=10)
    settings = Settings()
    cache_manager = MagicMock()
    cache_manager.get_result.return_value = None
    cache_manager.get_plan.return_value = None
    planner = MagicMock()

    scheduler = Scheduler(constraints, cache_manager, planner)
    resource_manager = ResourceManager(scheduler, constraints, settings, "test_hash", cache_manager)

    # 1. Test scheduling with channels
    task_id_a = scheduler.schedule_task("Task A", communication_channel="channel_1")
    task_id_b = scheduler.schedule_task("Task B", communication_channel="channel_1")
    task_id_c = scheduler.schedule_task("Task C", communication_channel="channel_2")

    assert scheduler.tasks[task_id_a].communication_channel == "channel_1"
    assert scheduler.tasks[task_id_b].communication_channel == "channel_1"
    assert scheduler.tasks[task_id_c].communication_channel == "channel_2"

    # 2. Test priority sort with channels
    task_ids = [task_id_a, task_id_b, task_id_c]
    priority_groups = scheduler.priority_sort(task_ids)

    # Should find "channel" group
    channel_group = next((g for g in priority_groups if g.name == "channel"), None)
    assert channel_group is not None
    assert set(channel_group.task_ids) == {task_id_a, task_id_b, task_id_c}

    # 3. Test prioritization by channel density
    # channel_1 has 2 tasks, channel_2 has 1 task.
    sorted_ids = resource_manager._prioritize_tasks_by_channel(task_ids)
    assert sorted_ids[0] in [task_id_a, task_id_b]
    assert sorted_ids[1] in [task_id_a, task_id_b]
    assert sorted_ids[2] == task_id_c

    # 4. Test communication tools
    tools_a = Tools(scheduler=scheduler, task_id=task_id_a, resource_manager=resource_manager)
    tools_b = Tools(scheduler=scheduler, task_id=task_id_b, resource_manager=resource_manager)

    # Task A shares data
    result_share = await tools_a.controller.registry.registry.actions["share_data"].function(
        channel="channel_1", data="Data from A"
    )
    assert "Data shared with 1 browsers" in result_share.extracted_content
    assert scheduler.tasks[task_id_b].shared_data[task_id_a] == "Data from A"

    # Task B gets shared data
    result_get = await tools_b.controller.registry.registry.actions["get_shared_data"].function(channel="channel_1")

    shared_data = json.loads(result_get.extracted_content.replace("Shared data: ", ""))
    assert shared_data[task_id_a] == "Data from A"

    # Task C should NOT see data from channel_1
    tools_c = Tools(scheduler=scheduler, task_id=task_id_c, resource_manager=resource_manager)
    result_get_c = await tools_c.controller.registry.registry.actions["get_shared_data"].function(channel="channel_2")
    shared_data_c = json.loads(result_get_c.extracted_content.replace("Shared data: ", ""))
    assert task_id_a not in shared_data_c

@pytest.mark.asyncio
async def test_share_data_with_targets():
    constraints = Constraints()
    scheduler = Scheduler(constraints, MagicMock(), MagicMock())
    resource_manager = MagicMock()

    tid_1 = scheduler.schedule_task("T1", communication_channel="ch")
    tid_2 = scheduler.schedule_task("T2", communication_channel="ch")
    tid_3 = scheduler.schedule_task("T3", communication_channel="ch")

    tools_1 = Tools(scheduler=scheduler, task_id=tid_1, resource_manager=resource_manager)

    # Share only with tid_2
    await tools_1.controller.registry.registry.actions["share_data"].function(
        channel="ch", data="secret", target_task_ids=tid_2
    )

    assert scheduler.tasks[tid_2].shared_data[tid_1] == "secret"
    assert scheduler.tasks[tid_3].shared_data is None or tid_1 not in scheduler.tasks[tid_3].shared_data

@pytest.mark.asyncio
async def test_channel_inheritance():
    constraints = Constraints()
    scheduler = Scheduler(constraints, MagicMock(), MagicMock())
    resource_manager = MagicMock()

    # Parent task with channel
    parent_id = scheduler.schedule_task("Parent", communication_channel="inherited_ch")

    tools = Tools(scheduler=scheduler, task_id=parent_id, resource_manager=resource_manager)

    # Launch subtask
    await tools.controller.registry.registry.actions["launch_subtask"].function(
        task="Subtask"
    )

    # Check if subtask inherited channel
    subtask_id = "B" # Next ID after Parent (A)
    assert subtask_id in scheduler.tasks
    assert scheduler.tasks[subtask_id].communication_channel == "inherited_ch"
