import os
import re
from typing import Optional, List, Text
from launch import LaunchDescriptionEntity
from launch import Action
from launch import LaunchDescription
from launch import LaunchDescriptionSource
from launch import LaunchContext
from launch.launch_description_sources import FrontendLaunchDescriptionSource
from launch.utilities import normalize_to_list_of_substitutions
from launch.utilities.type_utils import perform_typed_substitution

# actions
from launch.actions import IncludeLaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import GroupAction
from launch.actions import LogInfo

# substitution
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare

# exception
from launch.invalid_launch_file_error import InvalidLaunchFileError
from launch.substitutions.substitution_failure import SubstitutionFailure
from ament_index_python.packages import PackageNotFoundError

def remove_unnecessary_entities(context, entity, pattern, print_include_error=False):
    """
    부작용 있음. entity를 수정한다.
    entity 재활용 할 생각하지 말고
    이 함수의 return값을 사용하라.
    """

    def when_LaunchDescription(entity):
        entities = entity.entities.copy()
        entity.entities.clear()
        exist = False
        for sub in entities:
            tmp = rec(sub)
            if tmp is None:
                continue
            entity.add_entity(tmp[0])
            exist |= tmp[1]
        return (entity, exist) if entity.entities else None

    def when_IncludeLaunchDescription(entity):
        src = entity.launch_description_source

        def error_process(e):
            if print_include_error:
                return LogInfo(msg=f'remove_unnecessary_entities: {type(e).__name__}: ' + str(e)), False
            return None

        try:
            desc = src.get_launch_description(context) # must be before src.location
        except InvalidLaunchFileError as e:
            return error_process(e)
        except SubstitutionFailure as e:
            return error_process(e)
        except PackageNotFoundError as e:
            return error_process(e)

        if pattern.match(src.location):
            print('=' * 100)
            print(f'inc: {src.location}')
            print('=' * 100)
            return entity, True

        tmp = rec(desc)
        if tmp is None:
            return None

        new_desc, exist = tmp
        if not exist:
            return None

        desc.entities[:] = new_desc.entities
        return entity, True

    def when_GroupAction(entity):
        entities = entity.get_sub_entities().copy()
        entity.get_sub_entities().clear()
        exist = False
        for sub in entities:
            tmp = rec(sub)
            if tmp is None:
                continue
            entity.get_sub_entities().append(tmp[0])
            exist |= tmp[1]
        return (entity, exist) if entity.get_sub_entities() else None

    def rec(entity):
        if isinstance(entity, LaunchDescription):
            return when_LaunchDescription(entity)
        if isinstance(entity, IncludeLaunchDescription):
            return when_IncludeLaunchDescription(entity)
        if isinstance(entity, GroupAction):
            return when_GroupAction(entity)
        return entity, False

    return rec(entity)

def launch_to_path(launch: str) -> str:
    tmp = launch.split()
    assert 0 < len(tmp) <= 2

    if len(tmp) == 1:
        return launch

    pkg, file = tmp
    fps = FindPackageShare(pkg)
    return os.path.join(fps.find(pkg), "launch", file)

def cast_substitution(context, substitution, data_type):
    tmp = normalize_to_list_of_substitutions(substitution)
    return perform_typed_substitution(context, tmp, data_type)

class MyAction(Action):
    def __init__(self, src, dest, **kwargs):
        super().__init__(**kwargs)
        self.src = src
        self.dest = dest

    def visit(self, context: LaunchContext) -> Optional[List[LaunchDescriptionEntity]]:
        # config
        target_pkg_resolve_conf = LaunchConfiguration('target_pkg_resolve', default='true')
        target_pkg_resolve = cast_substitution(context, target_pkg_resolve_conf, bool)
        print_include_error_conf = LaunchConfiguration('print_include_error', default='false')
        print_include_error = cast_substitution(context, print_include_error_conf, bool)

        # launch
        config_launch = self.src.perform(context)
        target_launch = self.dest.perform(context)

        config_path = launch_to_path(config_launch)
        target = re.compile(launch_to_path(target_launch) if target_pkg_resolve else target_launch)

        config_front = FrontendLaunchDescriptionSource(config_path)
        config_desc = config_front.get_launch_description(context)

        tmp = remove_unnecessary_entities(context, config_desc, target, print_include_error)
        assert tmp is not None

        launch_desc, exist_target = tmp
        assert exist_target

        return [launch_desc]

def generate_launch_description():
    config_launch = LaunchConfiguration('config_launch')
    target_launch = LaunchConfiguration('target_launch', default='None')

    my_action = MyAction(config_launch, target_launch)

    return LaunchDescription([my_action])
