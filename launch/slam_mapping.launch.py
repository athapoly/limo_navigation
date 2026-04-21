# Copyright 2024 LIMO Workshop
# SPDX-License-Identifier: Apache-2.0
#
# Launch File: slam_mapping.launch.py
#
# Purpose: Start the full SLAM mapping pipeline for the LIMO robot in Gazebo.
# This launches:
#   1. Gazebo simulation with the LIMO differential-drive robot
#   2. slam_toolbox in online-async mode to build a 2-D occupancy-grid map
#   3. RViz2 pre-configured to display the map, LiDAR scan and robot TF tree
#
# Usage:
#   ros2 launch limo_navigation slam_mapping.launch.py
#   ros2 launch limo_navigation slam_mapping.launch.py world:=/abs/path/to/world.world
#
# After you are happy with the map, save it from a *separate* terminal:
#   ros2 run nav2_map_server map_saver_cli -f ~/maps/workshop_map
# ─────────────────────────────────────────────────────────────────────────────

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    # ── Package directories ──────────────────────────────────────────────────
    pkg_gazebo   = get_package_share_directory('limo_gazebosim')
    pkg_workshop = get_package_share_directory('limo_navigation')
    default_world = '/opt/ros/lcas/install/uol_tidybot/share/uol_tidybot/worlds/level_2_1.world'

    # ── Launch arguments ─────────────────────────────────────────────────────
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock',
    )
    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='Gazebo world file (default: existing level_2_1.world)',
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    world        = LaunchConfiguration('world')

    # ── 1. Gazebo + LIMO robot ───────────────────────────────────────────────
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo, 'launch', 'limo_gazebo_diff.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'world': world,
        }.items(),
    )

    # ── 2. slam_toolbox – online asynchronous SLAM ───────────────────────────
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

    # ── 3. RViz2 ─────────────────────────────────────────────────────────────
    rviz_config = os.path.join(pkg_workshop, 'rviz', 'slam_mapping.rviz')

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Delay slam_toolbox and RViz slightly so Gazebo can finish spawning
    delayed_slam = TimerAction(period=5.0, actions=[slam_toolbox_node])
    delayed_rviz = TimerAction(period=6.0, actions=[rviz_node])

    return LaunchDescription([
        use_sim_time_arg,
        world_arg,
        gazebo_launch,
        delayed_slam,
        delayed_rviz,
    ])
