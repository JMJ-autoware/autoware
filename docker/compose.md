# Compose

`docker-compose.yml` 파일과 그 종속성에 대해 설명한다.

## `launcher.sh`

compose 파일을 보면 `bash /my_launch/launcher.sh`와 같이 launch 스크립트 파일이 실행되는 것을 확인할 수 있다.

### 만들게된 배경

launch는 일반적으로 상위 launch 파일이 하위 launch 파일을 include하는 방식의 구조를 가진다. 예를 들어 `autoware_launch` package의 `planning_simulator.launch.xml`은 `autoware.launch.xml`과 `components/tier4_simulator_component.launch.xml`을 include한다. 이 두 하위 launch 파일을 다른 환경에서 launch시키기 위해서는 상위 launch 파일을 사용하지 않고 하위 launch 파일을 직접 launch해야 한다.

하위 launch 파일을 직접 launch하는 것은 다음과 같은 단점이 있다:

+ 상위 launch 파일에 정의된 arg를 사용할 수 없으므로, 직접 arg를 일일히 설정해 주어야 한다.
+ 각 launch 파일에 직접 arg를 설정해 주어야 하므로, 중복이 생길 수 있다.
+ 상위 launch 파일이 수정되면 하위 launch 파일에 넘기는 arg를 일일히 바꿔 주어야 한다.

따라서 하위 launch 파일을 직접 launch하지 않고 상위 파일을 사용하되, 원하는 launch 파일만 include하여 사용할 수 있도록 `launch.sh` 스크립트를 만들었다.

### 기본적인 동작 방식

1. `config_launch`와 `target_launch`를 launch arg로 받는다.
   + `config_launch`는 `target_launch`와 이름이 매칭되는 파일을 include하는 launch 파일이라고 가정한다. `config_launch`는 매칭되는 파일 외의 launch 파일도 include할 수 있다.
2. `config_launch`에서 `target_launch`와 이름이 매칭되는 파일을 include하는 [include launch description](https://docs.ros.org/en/ros2_packages/humble/api/launch/architecture.html#basic-actions)을 제외한 모든 include launch description을 제거한다.
3. include launch description이 제거된 `config_launch`를 launch한다.

### 명세

+ **argument**: `launcher.sh`의 argument는 `ros2 launch` 스타일(`arg_name:=value`)로 설정해 주어야 한다.

  + `config_launch`: 하위 launch 파일(`target_launch`)를 include하는 상위 launch 파일의 위치를 지정.

    + `launch_to_path` 함수를 사용하여 변환된다.

    + `target_launch`: 제거되지 않을 include를 지정한다. 즉, include하고 싶은, 남겨두고 싶은 하위 launch 파일을 지정한다.
      + xml launch 파일을 기준으로 설명하면, `target_launch`는  `include` tag의 `file` attribute와 매칭되는지 확인된다. 매칭 작업에는 python의 정규 표현식이 사용된다.
      + `launch_to_path` 함수를 사용하여 변환된다. `target_pkg_resolve` arg를 `false`로 지정하여 `launch_to_path`를 수행하지 않도록 할 수 있다. `target_pkg_resolve`의 기본값은 `true`이다.

  + `target_pkg_resolve`: `target_launch`가 `launch_to_path`를 사용하여 변환될지 여부를 결정한다.

  + `print_include_error`: include되는 launch 파일의 launch description을 얻어내지 못했을 경우에 로그를 출력할지 여부를 결정한다.
    + 로그 출력은 `LogInfo` [action](https://docs.ros.org/en/ros2_packages/humble/api/launch/architecture.html#actions)을 사용하여 수행된다.
    + 기본값은 `false`이다.
    + 대상이 되는 include launch 파일 외의 하위 launch 파일은 해당 환경에 존재하지 않을 수 있기 때문에 불필요한 include error를 줄이기 위함이다.

+ **funciton**: 함수는 `launcher.sh` 밖에서는 보이지 않지만 이해를 위해 설명을 적는 것이 유용할 것 같다. 파이썬이다.

  + `launch_to_path`: launch 파일을 지정하는 문자열을 받아 해당 launch 파일의 경로를 반환한다.

    + **동작 방식**:
      1. `launch` 매개변수를 받는다. 이는 문자열이다.
      2. `launch.split()`을 사용하여 나눈다.
      3. 나뉘어진 것은 원소 개수가 1 또는 2여야 한다.
      4. 원소 개수가 1이면 아무 처리도 하지 않고 반환한다.
      5. 원소 개수가 2면 첫 번째 원소를 package로 간주하고, 두 번째 원소를 launch 파일 이름으로 간주하여, 이 둘을 사용하여 launch 파일의 경로를 얻어내서 반환한다.

    + **예시**:
      + `launch_to_path("asdf.launch.xml") -> "asdf.launch.xml"`
      + `launch_to_path("autoware_launch autoware.launch.xml") -> "/opt/autoware/share/autoware_launch/launch/autoware.launch.xml"`

### 사용 예

```bash
  bash launcher.sh \
  config_launch:="autoware_launch planning_simulator.launch.xml" \
  target_launch:="autoware_launch autoware.launch.xml" \
  map_path:=/autoware_map \
  vehicle_model:=sample_vehicle \
  sensor_model:=sample_sensor_kit \
  rviz:=false \
  print_include_error:=false \
```

`planning_simulator.launch.xml`은 `autoware.launch.xml`과 `components/tier4_simulator_component.launch.xml`을 include하는데, `launcher.sh`는 `components/tier4_simulator_component.launch.xml` include를 없애고 `autoware.launch.xml` include만을 남겨놓는다.

## Note

+ `launcher.sh`는 내부적으로 같은 디렉토리에 있는 `launcher.launch.py`를 launch한다.
  + `ros2 launch "$SCRIPT_DIR/launcher.launch.py" "$@"`
+ 현재 docker compose 파일에선 컨테이너 이미지에 `launcher.sh`를 넣지 않고 `launcher.sh`가 있는 디렉토리를 마운트하여 사용하도록 되어있다.
+ docker compose 파일의 컨테이너 명세에 `autoware_launch planning_simulator.launch.xml`가 지정되어 있는 것을 볼 수 있다. 여기서 launch되는 `planning_simulator.launch.xml`은 각각 다른 컨테이너에 있는 서로 다른 launch 파일이 launch되는 것이다.
