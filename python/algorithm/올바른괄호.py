def solution(s):

    # 올바른 괄호 란 것을 만들고 싶습니다.
    # 열린 괄호 : +1
    # 닫힌 괄호 : -1


    # edge case
    # 1 : )( -> 합은 0이지만, 닫히고 열리기 때문에 안됨.
    # -> 
    value = 0
    for char in s:
        if char == '(':
            value += 1
        elif char == ')':
            value -= 1

        # 1번째에 대한 해결책
        if value < 0:
            return False

    if value == 0:
        return True
    else:
        return False


print(solution("(())()"))      # True
print(solution("(()(")  )      # False     # 열리는게 더 많은 경우
print(solution("(()())))") )   # False     # 닫히는게 더 많은 경우
print(solution(")()(")     )   # False     # 개수는 같지만, 닫히는게 먼저 오는 경우.


# 확장 -> () -> () , {}, []
from collections import deque
def solution(s):

    stack = deque() # list를 써도 무방하긴 합니다.
    open_blanket = {'(', '{', '['}

    blanket_mapping = {
        ']' : '[',
        '}' : '{',
        ')' : '(',
    }
    # 열린게 들어와 -> stack에 넣어줘.
    # 닫힌게 들어와 -> stack의 가장 뒤의 녀석을 확인해서
        # 쌍이 맞으면 성공
        # 쌍이 맞지 않으면 실패

    for char in s:
        # list보다는 set이 `in`에 대해 속도가 빠름.
        # list -> O(n) / set -> O(1)
        if char in open_blanket:
            stack.append(char)

        # elif char == ']':
        #     # stack의 맨 뒤는 [ 여야 해.
        # elif char == '}':
        #     # stack의 맨 뒤는 { 여야 해.
        # elif char == ')':
        #     # stack의 맨 뒤는 ( 여야 해.
        # elif char 가 닫히는 것
        #     stack의 맨 뒤는 blanket_mapping[char] 여야 해.

        # 문제 조건에서 괄호만 있다 라고 적혀있으면 else: 로 써도 무방합니다.
        elif char in blanket_mapping.keys(): # char가 닫히는 것 이라면.

            # stack이 비어있는 상태에서 닫히는게 들어오면 False
            # 즉, 닫히는게 더 많은 경우
            if not stack:
                return False
            
            # 쌍이 맞지 않는 경우
            if stack[-1] != blanket_mapping[char]:
                return False
            
            stack.pop()
    

    # 열리는게 남아있는 경우도 있습니다.
    if stack:
        return False
    
    return True

print()
print(solution("[{}][()]"))         # True
print(solution("([{}][()]")  )      # False     # 열리는게 더 많은 경우
print(solution("[{}][()])") )       # False     # 닫히는게 더 많은 경우
print(solution("[{)][()]"))         # False     # 쌍이 맞지 않는 경우.
