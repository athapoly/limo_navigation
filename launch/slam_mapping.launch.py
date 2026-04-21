# Copyright 2024 LIMO Workshop
# SPDX-License-Identifier: Apache-2.0
#
# Launch File: slam_mapping.launch.py
#
# Purpose: Start the SLAM mapping pipeline for the LIMO robot.
# Assumes the Gazebo simulation is already running via:
#   ros2 launch uol_tidybot tidybot.launch.py world:=level_2_1.world
#
# This launches:
#   1. slam_toolbox in online-async mode to build a 2-D occupancy-grid map
#   2. RViz2 pre-configured to display the map, LiDAR scan and robot TF tree
#
# Usage:
#   ros2 launch limo_navigation slam_mapping.launch.py
#
# After you are happy with the map, save it from a *separate* terminal:
#   ros2 run nav2_map_server map_saver_cli -f ~/maps/workshop_map
# ─────────────────────────────────────────────────────────────────────────────

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    TimerAction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # ── Package directories ──────────────────────────────────────────────────
    pkg_workshop = get_package_share_directory('limo_navigation')

    # ── Launch arguments ─────────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')

    # ── 1. slam_toolbox – online asynchronous SLAM ───────────────────────────
    slam_params = os.path.join(pkg_workshop, 'params', 'slam_toolbox_online.yaml')

    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            slam_params,
            {'use_sim_time': use_sim_time},
        ],
    )

    # ── 2. RViz2 ─────────────────────────────────────────────────────────────
    rviz_config = os.path.join(pkg_workshop, 'rviz', 'slam_mapping.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Delay RViz slightly to allow slam_toolbox to initialise first
    delayed_rviz = TimerAction(period=3.0, actions=[rviz_node])

    return LaunchDescription([
        use_sim_time_arg,
        slam_toolbox_node,
        delayed_rviz,
    ])
