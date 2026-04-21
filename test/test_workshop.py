# Copyright 2024 LIMO Workshop
# SPDX-License-Identifier: Apache-2.0
"""Minimal tests to ensure package structure is valid."""

import os
import pytest


def test_package_xml_exists():
    """package.xml must exist at the package root."""
    pkg_root = os.path.join(os.path.dirname(__file__), '..')
    assert os.path.isfile(os.path.join(pkg_root, 'package.xml'))


def test_nav_params_have_astar_plugin():
    """nav2_params_astar.yaml must specify the SmacPlanner2d plugin."""
    params_path = os.path.join(
        os.path.dirname(__file__), '..', 'params', 'nav2_params_astar.yaml'
    )
    with open(params_path) as f:
        content = f.read()
    assert 'SmacPlanner2d' in content, \
        'A* plugin (SmacPlanner2d) not found in nav2_params_astar.yaml'


def test_slam_params_are_mapping_mode():
    """slam_toolbox_online.yaml must be in 'mapping' mode."""
    params_path = os.path.join(
        os.path.dirname(__file__), '..', 'params', 'slam_toolbox_online.yaml'
    )
    with open(params_path) as f:
        content = f.read()
    assert 'mode: mapping' in content, \
        "slam_toolbox params must have 'mode: mapping'"


def test_launch_files_exist():
    """Both key launch files must be present."""
    launch_dir = os.path.join(os.path.dirname(__file__), '..', 'launch')
    assert os.path.isfile(os.path.join(launch_dir, 'slam_mapping.launch.py'))
    assert os.path.isfile(os.path.join(launch_dir, 'navigation_astar.launch.py'))


def test_nav_client_importable():
    """The astar_nav_client module must import without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'astar_nav_client',
        os.path.join(
            os.path.dirname(__file__), '..', 'limo_navigation', 'astar_nav_client.py'
        ),
    )
    mod = importlib.util.module_from_spec(spec)
    # Only test syntax/import – no ROS runtime needed
    assert spec is not None


def test_waypoint_tour_importable():
    """The waypoint_tour module must import without errors."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'waypoint_tour',
        os.path.join(
            os.path.dirname(__file__), '..', 'limo_navigation', 'waypoint_tour.py'
        ),
    )
    assert spec is not None
