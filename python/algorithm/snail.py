# 다음 2차원 배열을 만들어보세요.

#  1  2  3  4  5
# 16 17 18 19  6
# 15 24 25 20  7
# 14 23 22 21  8
# 13 12 11 10  9

n = 5

# 2차원 배열에 숫자를 채워넣기 위해서
# 1. 리스트를 만들어서 하나하나 집어넣는다
    # [] -> [[]] -> [[1, 2, 3, 4]] -> [[1, 2, 3, 4], [5, 6, 7, 8]]
# 2. 미리 특정 사이즈의 2차원 배열을 만들어서 값만 넣는다.

from pprint import pprint
snail = [[0]*n for _ in range(n)]

# snail = []

# for _ in range(n): # n번 반복할꺼야.
#     snail.append([0] * n)

pprint(snail)

# 왼쪽 위에서 시작해서 
# 숫자를 하나씩 키워가면서 
# 한칸씩 이동을한다.

# 기초 정보
i = 0
j = 0
num = 1

# 방향성을 특정지어야 함.
#     우  하  좌  상
di = [0, 1, 0, -1]
dj = [1, 0, -1, 0]

# 우리의 진행 방향.
d = 0

# 1넣기
snail[i][j] = num

print()
pprint(snail)

# 2 넣기
num += 1

i = i + di[d]
j = j + dj[d]

snail[i][j] = num
print()
pprint(snail)

# 3 넣기
num += 1

i = i + di[d]
j = j + dj[d]

snail[i][j] = num
print()
pprint(snail)