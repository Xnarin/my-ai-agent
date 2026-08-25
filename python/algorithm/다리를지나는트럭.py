from collections import deque
def solution(bridge_length, weight, truck_weights):
    answer = 0

    # truck_weights에 들어있는 트럭들을
    # bridge_length라고 되어있는 queue에 하나씩 통과를 시켜서
    # 시간을 재고 싶다.

    # 단, bridge는 무게 제한이 있다.

    # 1. bridge에 truck_weights의 첫번째 트럭 넣기.
    # 2. bridge위의 첫번째 트럭을 왼쪽으로 옮기고, 
    #    truck_weights의 다음 트럭 준비시키기.
        # 만약 들어가면 넣기
        # 안들어가면 기다리기
        # 언젠가는 들어감.
    #    ....

    bridge = deque([0]*bridge_length) # qeueue.
    bridge_weight = 0 # 다리에 있는 버스들의 무게
    ready_truck_index = 0

    time = 0
    # bridge_weight > 0 => 다리에 아직 버스가 있다.
    # ready_truck_index < len(truck_weights) -> 준비된 버스가 있다.

    while bridge_weight > 0 or ready_truck_index < len(truck_weights): 
        out_bus = bridge.popleft() # 원래 있던 버스 빼기.
        bridge_weight -= out_bus    # 나간 버스만큼 무게가 빠진다.


        # 버스 준비시키기.
        # 다리 위의 무게 + 준비한 버스의 무게 <= 버틸 수 있는 무게
        # 이동을 시킬 수 있음.
        # ready_truck_index < len(truck_weights) -> 준비된 트럭이 존재할때만 아래 코드를 진행해.
   

        if ready_truck_index < len(truck_weights) and bridge_weight + truck_weights[ready_truck_index] <= weight:

            truck = truck_weights[ready_truck_index]

            bridge.append(truck)
            bridge_weight += truck
            ready_truck_index += 1
        else:
            bridge.append(0) # 빈공간 채워주기
            # bridge_weight += 0
            # ready_truck_index 변함이 없습니다.

        time += 1

    return time