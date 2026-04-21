# Copyright 2024 LIMO Workshop
# SPDX-License-Identifier: Apache-2.0
"""
waypoint_tour.py
────────────────
Sends a sequence of waypoints to Nav2's NavigateThroughPoses action server.
The robot visits each waypoint in order using the A* global planner.

Usage:
    ros2 run limo_navigation waypoint_tour

The default tour visits four corners of a 2 m square around the origin.
Edit WAYPOINTS below (or pass --waypoints as a JSON string) to customise.

Pre-requisites:
  - Gazebo simulation running
  - navigation_astar.launch.py running
"""

import json
import math
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped, Quaternion
from nav2_msgs.action import NavigateThroughPoses


# Default waypoints: (x, y, yaw_deg)
WAYPOINTS = [
    (2.0,  0.0,   0.0),
    (2.0,  2.0,  90.0),
    (0.0,  2.0, 180.0),
    (0.0,  0.0, -90.0),
]


def yaw_to_quaternion(yaw_deg: float) -> Quaternion:
    yaw = math.radians(yaw_deg)
    q = Quaternion()
    q.z = math.sin(yaw / 2.0)
    q.w = math.cos(yaw / 2.0)
    return q


def make_pose(node: Node, x: float, y: float, yaw_deg: float) -> PoseStamped:
    ps = PoseStamped()
    ps.header.frame_id = 'map'
    ps.header.stamp    = node.get_clock().now().to_msg()
    ps.pose.position.x = x
    ps.pose.position.y = y
    ps.pose.orientation = yaw_to_quaternion(yaw_deg)
    return ps


class WaypointTour(Node):
    def __init__(self, waypoints):
        super().__init__('waypoint_tour')
        self._waypoints = waypoints
        self._done = False
        self._client = ActionClient(self, NavigateThroughPoses,
                                    'navigate_through_poses')

    def send_tour(self):
        self.get_logger().info('Waiting for NavigateThroughPoses server…')
        self._client.wait_for_server()

        poses = [make_pose(self, x, y, yaw) for x, y, yaw in self._waypoints]
        goal = NavigateThroughPoses.Goal()
        goal.poses = poses

        self.get_logger().info(
            f'Starting waypoint tour – {len(poses)} waypoints'
        )
        fut = self._client.send_goal_async(goal,
                                           feedback_callback=self._feedback_cb)
        fut.add_done_callback(self._goal_response_cb)

    def is_done(self):
        return self._done

    def _goal_response_cb(self, future):
        gh = future.result()
        if not gh.accepted:
            self.get_logger().error('Tour goal REJECTED.')
            self._done = True
            return
        self.get_logger().info('Tour ACCEPTED – following waypoints…')
        self._result_future = gh.get_result_async()
        self._result_future.add_done_callback(self._result_cb)

    def _feedback_cb(self, feedback_msg):
        fb = feedback_msg.feedback
        self.get_logger().info(
            f'  Waypoints remaining: {fb.number_of_poses_remaining}'
            f'  | Distance remaining: {fb.distance_remaining:.2f} m'
        )

    def _result_cb(self, future):
        status = future.result().status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info('✔  Waypoint tour COMPLETE!')
        else:
            self.get_logger().warn(f'Tour ended with status: {status}')
        self._done = True


def main(args=None):
    rclpy.init(args=args)

    waypoints = WAYPOINTS
    for arg in sys.argv[1:]:
        if arg.startswith('--waypoints='):
            waypoints = json.loads(arg.split('=', 1)[1])

    node = WaypointTour(waypoints)
    node.send_tour()
    try:
        while rclpy.ok() and not node.is_done():
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
